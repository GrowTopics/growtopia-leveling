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

@client.event
async def on_message(message):
    if message.content.startswith("<!"):
        await client.process_commands(message)
    else:
        if str(message.author.id) not in ON_COOLDOWN and not(message.author.bot) and len(message.content.split(" "))>1:
            print(message.author.name)
            if str(message.author.id) not in USERS:
                e = discord.Embed(
                    title = f"Welcome {message.author.name}!",
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

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        em = discord.Embed(title=f"Slow it down bro!",description=f"Try again in {error.retry_after:.2f}s.", color=discord.Colour.red())
        await ctx.send(embed=em)
    else:
        print(error)

@client.command('check')
async def check_command(ctx):
    if ctx.author.id not in [852572302590607361,591107669180284928,309301527934140418]:
        return
    e = discord.Embed(title=f"Variable: `ON_COOLDOWN`",description=f"```\n{ON_COOLDOWN}\n```").set_footer(text=f"{TO_Next} seconds till next upload")
    await ctx.send(embed=e)
    e = discord.Embed(title=f"Variable: `XP_COUNT` - Uploads every 5 Minutes",description=f"```\n{XP_COUNT}\n```")
    await ctx.send(embed=e)

@client.command(name="leaderboard",aliases=["lb"])
@commands.cooldown(1, 30, commands.BucketType.guild)
async def leaderboard_cmd(ctx):
    async with ctx.typing():
        sheet = SPREAD.worksheet("Leveling")
        iden,xps,ordered = list(map(int,sheet.col_values(1)[1:])),list(map(int,sheet.col_values(2)[1:])),[]
        await client.wait_until_ready()
        while iden!=[] and xps!=[]:
            index = xps.index(max(xps))
            ordered.append([await client.fetch_user(iden[index]),xps[index]])
            iden.pop(index)
            xps.pop(index)
        print(ordered)
        phr = [f"{i[0]}    `{i[1]}`" for i in ordered]
        embed = discord.Embed(
            title = "Global Leaderboard",
            description = "\n".join(phr),
            colour = discord.Colour.blurple()
        )
    await ctx.send(embed=embed)

@client.command(aliases=['sb'])
async def superbroadcast(ctx):
    if ctx.author.id == 591107669180284928:
        await ctx.send(
            "Type in What You want to broadcast\n`Type cancel to force end`")
        msg = await client.wait_for('message', check=lambda m:m.author.id == 591107669180284928)
        if msg.content != "" and msg.content != "cancel":
            for i in client.guilds:
              channel = i.system_channel
              await channel.send(
                        f"**Super Broadcast**\n{msg.content}\n\n*By my creator The UKNOWN...*"
                    )
            await ctx.send("Broadcast Successfully Sent!")
        else:
            await ctx.send("`Super Broadcast Cancelled.`")

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
        await client.get_channel(867533836803244042).send(embed=e)

@tasks.loop(seconds=5)
async def change_p():
    statuses = [f"{len(client.guilds)} Servers","you talk","Growtopia Leveling System"]
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(statuses)))

@change_p.before_loop
@update_cooldown.before_loop
async def check_ready():
    await client.wait_until_ready()

#Run Background tasks
bg_tasks = [update_cooldown,upload_data,change_p]
for i in bg_tasks:
    i.start()

client.run(os.getenv('token'))
