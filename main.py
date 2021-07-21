import discord,os,gspread,time,socket,datetime,random
from discord.ext import commands,tasks
from oauth2client.service_account import ServiceAccountCredentials as sac

client = commands.Bot(command_prefix="<!")

#Important Global Variables
ON_COOLDOWN = {}
XP_COUNT = {}

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = sac.from_json_keyfile_name("levelingclient.json", scope)
google_client = gspread.authorize(creds)
SPREAD = google_client.open_by_key("1KTrNOXZXdbOg9rALPxxkys5jEDU-cOuzOB_jtJEDpbg")

points_per_msg = random.choice(list(range(5,15)))
upload_interval = 10    #Minutes
points_award_cooldown = 10

TO_Next = upload_interval*60
development = False     #Set to False when pushing

def log(text=""):
    if development == True:
        print(text)

@client.event
async def on_ready():
    global USERS
    print(f"Bot Already Online...Running on {socket.gethostname()}")
    if development == False:
        await client.get_channel(847602473627025448).send(embed=discord.Embed(
            title = "Bot Status",
            description = "Running on `%%hostname%%` at `%%datetime%%`".replace("%%hostname%%",socket.gethostname()).replace("%%datetime%%",datetime.datetime.now().strftime('%c')),
            colour = discord.Colour(0xd81b60)
        ).set_footer(text="Server Time Now: %%server_time%%".replace("%%server_time%%",datetime.datetime.now().strftime("%H:%M:%S"))))

    USERS = SPREAD.worksheet("Leveling").col_values(1)
    log(f"Fetched Information {random.choice(['Alpha','Bravo','Charlie','Delta','Echo','Foxtrot','Golf','Hotel','India','Juliet'])}!!!")
    update_cooldown.start()
    upload_data.start()

@client.event
async def on_message(message):
    if message.content.startswith("<!"):
        await client.process_commands(message)
    else:
        if str(message.author.id) not in ON_COOLDOWN and not(message.author.bot):

            if str(message.author.id) not in USERS:
                e = discord.Embed(
                    title = f"Welcome {client.get_user(message.author.name)}!!!",
                    description = "Participating in conversations help you level up.\nSpam Detection has been enabled - Don't try it",
                    colour = discord.Colour.green()
                )
                await message.channel.send(embed=e)
                USERS.append(str(message.author.id))

            ON_COOLDOWN[str(message.author.id)] = points_award_cooldown
            if str(message.author.id) not in XP_COUNT:
                XP_COUNT[str(message.author.id)] = points_per_msg
            else:
                XP_COUNT[str(message.author.id)] = XP_COUNT[str(message.author.id)] + 10


@client.command('check')
async def check_command(ctx):
    if ctx.author.id not in [852572302590607361,591107669180284928,309301527934140418]:
        return
    e = discord.Embed(title=f"Variable: `ON_COOLDOWN`",description=f"```\n{ON_COOLDOWN}\n```").set_footer(text=f"{TO_Next} seconds till next upload")
    await ctx.send(embed=e)
    e = discord.Embed(title=f"Variable: `XP_COUNT` - Uploads every 5 Minutes",description=f"```\n{XP_COUNT}\n```")
    await ctx.send(embed=e)

@tasks.loop(seconds=1)
async def update_cooldown():
    global TO_Next
    log(f"{ON_COOLDOWN}\t\t{XP_COUNT}")
    cool_over = []
    for i in ON_COOLDOWN:
        ON_COOLDOWN[i] = ON_COOLDOWN[i]-1
        if ON_COOLDOWN[i]<=0:
            cool_over.append(i)
    for i in cool_over:
        log(f"Cooldown Over for {i}")
        del ON_COOLDOWN[i]

    TO_Next -= 1
    if TO_Next == 0:
        TO_Next = upload_interval*60

@tasks.loop(minutes=upload_interval)
async def upload_data():
    global XP_COUNT,USERS
    if XP_COUNT != {}:
        sheet = SPREAD.worksheet("Leveling")
        USERS = sheet.col_values(1)
        cell_updates,new_count = [],0
        start = time.time()
        for i in XP_COUNT:
            if i in USERS:
                cell_updates.append(gspread.models.Cell(row=USERS.index(i)+1,col=2,value=int(sheet.acell(f"B{USERS.index(i)+1}").value)+XP_COUNT[i]))
            else:
                cell_updates.append(gspread.models.Cell(row=len(USERS)+new_count+1,col=1,value=i))
                cell_updates.append(gspread.models.Cell(row=len(USERS)+new_count+1,col=2,value=XP_COUNT[i]))
                cell_updates.append(gspread.models.Cell(row=len(USERS)+new_count+1,col=3,value=1))
                cell_updates.append(gspread.models.Cell(row=len(USERS)+new_count+1,col=4,value=datetime.datetime.now().strftime("%c")))
                new_count+=1
        sheet.update_cells(cell_updates)
        log("Uploaded Data!!!")
        USERS = sheet.col_values(1)
        code_fetch = random.choice(['Alpha','Bravo','Charlie','Delta','Echo','Foxtrot','Golf','Hotel','India','Juliet'])
        log(f"Fetched Information {code_fetch}!!!")
        XP_COUNT = {}
        e = discord.Embed(title="Upload Data",description="\n".join(map(str,cell_updates)),colour=discord.Colour(0x232323)).set_footer(text=f"Uploaded in {time.time()-start} seconds. Fetched information {code_fetch}")
        await client.get_channel(856225104161275964).send(embed=e)

@update_cooldown.before_loop
async def check_ready():
    await client.wait_until_ready()

client.run(os.getenv('token'))
