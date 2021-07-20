import discord,os,gspread,time,socket,datetime
from discord.ext import commands,tasks
from oauth2client.service_account import ServiceAccountCredentials as sac

client = commands.Bot(command_prefix="<!")

#Important Global Variables
ON_COOLDOWN = {}
XP_COUNT = {}

points_per_msg = 10
upload_interval = 300
points_award_cooldown = 15


development = False     #Set to False when pushing

def log(text=""):
    if development == True:
        print(text)

@client.event
async def on_ready():
    print(f"Bot Already Online...Running on {socket.gethostname()}")
    await client.get_channel(856225104161275964).send(embed=discord.Embed(
        title = "Bot Status",
        description = "Running on `%%hostname%%` at `%%datetime%%`".replace("%%hostname%%",socket.gethostname()).replace("%%datetime%%",datetime.datetime.now().strftime('%c')),
        colour = discord.Colour(0xd81b60)
    ).set_footer(text="Server Time Now: %%server_time%%".replace("%%server_time%%",datetime.datetime.now().strftime("%H:%M:%S"))))
    update_cooldown.start()
    upload_data.start()

@client.event
async def on_message(message):
    if message.content.startswith("<!"):
        await client.process_commands(message)
    else:
        if str(message.author.id) not in ON_COOLDOWN and message.author!=client.user:
            ON_COOLDOWN[str(message.author.id)] = points_award_cooldown
            if str(message.author.id) not in XP_COUNT:
                XP_COUNT[str(message.author.id)] = points_per_msg
            else:
                XP_COUNT[str(message.author.id)] = XP_COUNT[str(message.author.id)] + 10


@client.command('check')
async def check_command(ctx):
    if ctx.author.id not in [852572302590607361,591107669180284928,309301527934140418]:
        return
    e = discord.Embed(title=f"Variable: `ON_COOLDOWN`",description=f"```\n{ON_COOLDOWN}\n```")
    await ctx.send(embed=e)
    e = discord.Embed(title=f"Variable: `XP_COUNT` - Uploads every 5 Minutes",description=f"```\n{XP_COUNT}\n```")
    await ctx.send(embed=e)

@tasks.loop(seconds=1)
async def update_cooldown():
    log(f"{ON_COOLDOWN}\t\t{XP_COUNT}")
    cool_over = []
    for i in ON_COOLDOWN:
        ON_COOLDOWN[i] = ON_COOLDOWN[i]-1
        if ON_COOLDOWN[i]<=0:
            cool_over.append(i)
    for i in cool_over:
        log(f"Cooldown Over for {i}")
        del ON_COOLDOWN[i]

@tasks.loop(seconds=upload_interval)
async def upload_data():
    global XP_COUNT
    if XP_COUNT != {}:
        scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
        creds = sac.from_json_keyfile_name("levelingclient.json", scope)
        google_client = gspread.authorize(creds)
        spread = google_client.open_by_key("1KTrNOXZXdbOg9rALPxxkys5jEDU-cOuzOB_jtJEDpbg")
        sheet = spread.worksheet("Leveling")
        users = sheet.col_values(1)
        cell_updates,new_count = [],0
        start = time.time()
        for i in XP_COUNT:
            if i in users:
                cell_updates.append(gspread.models.Cell(row=users.index(i)+1,col=2,value=int(sheet.acell(f"B{users.index(i)+1}").value)+XP_COUNT[i]))
            else:
                cell_updates.append(gspread.models.Cell(row=len(users)+new_count+1,col=1,value=i))
                cell_updates.append(gspread.models.Cell(row=len(users)+new_count+1,col=2,value=XP_COUNT[i]))
                cell_updates.append(gspread.models.Cell(row=len(users)+new_count+1,col=3,value=1))
                cell_updates.append(gspread.models.Cell(row=len(users)+new_count+1,col=4,value=datetime.datetime.now().strftime("%c")))
                new_count+=1
                e = discord.Embed(
                    title = f"Welcome {i}!!!",
                    description = "Participating in conversations help you level up.\nSpam Detection has been enabled - Don't try it",
                    colour = discord.Colour.green()
                )
                await ctx.send(embed=e)
        sheet.update_cells(cell_updates)
        log("Uploaded Data!!!")
        XP_COUNT = {}
        e = discord.Embed(title="Upload Data",description="\n".join(map(str,cell_updates)),colour=discord.Colour(0x232323)).set_footer(text=f"Uploaded in {time.time()-start} seconds")
        await client.get_channel(856225104161275964).send(embed=e)

@update_cooldown.before_loop
async def check_ready():
    await client.wait_until_ready()

client.run(os.getenv('token'))
