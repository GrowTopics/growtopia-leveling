import discord,os,gspread,time,socket,datetime,random
from discord.ext import commands,tasks
from oauth2client.service_account import ServiceAccountCredentials as sac
from discord.utils import get

intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix="<!",intents=intents)

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
xp_levelup = list(map(int,SPREAD.worksheet("Settings").row_values(2)))

TO_Next = upload_interval*60
development = False     #Set to False when pushing

def log(text=""):
    if development == True:
        print(text)

#Self Healing
async def self_healing():
    sheet = SPREAD.worksheet("Leveling")
    to_delete = []
    column1 = sheet.col_values(1).copy()
    for i in range(len(column1)):
        if column1[i].endswith("00"):
            to_delete.append(i+1)
            await client.get_channel(847602473627025448).send(embed=discord.Embed(title="Self Fixing has Found a Faulty ID",description=f"**Deleted row** `{i+1}`\nFaulty ID: `{column1[i]}`"))
    for i in to_delete:
        sheet.delete_rows(i)

@client.event
async def on_ready():
    global USERS,RAW,USERNAMES
    log(f"Bot Already Online...Running on {socket.gethostname()}")
    RAW = SPREAD.worksheet("Leveling").get_all_values()[1:]
    for i in range(len(RAW)):
        RAW[i][1],RAW[i][2] = int(RAW[i][1]),int(RAW[i][2])
    USERS = [i[0] for i in RAW]
    while True:
        USERNAMES = []
        for i in USERS:
            try:
                USERNAMES = [client.get_user(int(i)) for i in USERS]
            except Exception as e:
                # Execute Self Healing Protocol
                await self_healing()
                continue
        break

    log(f"Fetched Information {random.choice(['Alpha','Bravo','Charlie','Delta','Echo','Foxtrot','Golf','Hotel','India','Juliet'])}!!!")
    if development == False:
        await client.get_channel(847602473627025448).send(embed=discord.Embed(
            title = "Bot Status",
            description = "Running on `%%hostname%%` at `%%datetime%%`".replace("%%hostname%%",socket.gethostname()).replace("%%datetime%%",datetime.datetime.now().strftime('%c')),
            colour = discord.Colour(0xd81b60)
        ).set_footer(text="Server Time Now: %%server_time%%".replace("%%server_time%%",datetime.datetime.now().strftime("%H:%M:%S"))))

@client.event
async def on_message(message):
    global USERS,RAW
    if message.content.startswith("<!"):
        await client.process_commands(message)
    else:
        if str(message.author.id) not in ON_COOLDOWN and not(message.author.bot) and len(message.content.split(" "))>1:

            if str(message.author.id) not in USERS:
                timenow = datetime.datetime.now().strftime("%c")
                new_user = [
                    gspread.models.Cell(row=len(USERS)+1,col=1,value=message.author.id),
                    gspread.models.Cell(row=len(USERS)+1,col=2,value=0),
                    gspread.models.Cell(row=len(USERS)+1,col=3,value=1),
                    gspread.models.Cell(row=len(USERS)+1,col=4,value=timenow)
                ]
                await client.get_channel(847602473627025448).send(embed=discord.Embed(
                    title = "New User",
                    description = "".join(list(map(str,new_user))),
                    colour = discord.Colour.orange()
                ).set_footer(text="Server Time Now: %%server_time%%".replace("%%server_time%%",datetime.datetime.now().strftime("%H:%M:%S"))))

                RAW.append([str(message.author.id),0,1,timenow])
                SPREAD.worksheet("Leveling").update_cells(new_user)
                USERS.append(str(message.author.id))

            ON_COOLDOWN[str(message.author.id)] = points_award_cooldown

            assign_points = points_per_msg
            if str(message.author.id) not in XP_COUNT:
                XP_COUNT[str(message.author.id)] = assign_points
            else:
                XP_COUNT[str(message.author.id)] = XP_COUNT[str(message.author.id)] + assign_points
            RAW[USERS.index(str(message.author.id))][1] = RAW[USERS.index(str(message.author.id))][1] + assign_points

            #Check if Level Up

            if RAW[USERS.index(str(message.author.id))][1] >= xp_levelup[RAW[USERS.index(str(message.author.id))][2]+1]:
                RAW[USERS.index(str(message.author.id))][2] = RAW[USERS.index(str(message.author.id))][2]+1
                e = discord.Embed(
                    title = f"**Congratulations** {message.author.name}!\nYou have Reached **LEVEL** `{RAW[USERS.index(str(message.author.id))][2]}`\n🥳 🥳 🥳",
                    colour = discord.Colour.teal()
                )
                await message.channel.send(embed=e)
                SPREAD.worksheet("Leveling").update(f"C{USERS.index(str(message.author.id))+2}",RAW[USERS.index(str(message.author.id))][2])

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        em = discord.Embed(title=f"You or your Server is under Command Cooldown",description=f"Try again in {error.retry_after:.2f}s.", color=discord.Colour.red())
        await ctx.send(embed=em)
    else:
        raise error

@client.command('check')
async def check_command(ctx):
    if ctx.author.id not in [852572302590607361,591107669180284928,309301527934140418]:
        return
    e = discord.Embed(title=f"Variable: `ON_COOLDOWN`",description=f"```\n{ON_COOLDOWN}\n```").set_footer(text=f"{TO_Next} seconds till next upload")
    await ctx.send(embed=e)
    e = discord.Embed(title=f"Variable: `XP_COUNT` - Uploads every 5 Minutes",description=f"```\n{XP_COUNT}\n```")
    await ctx.send(embed=e)

@client.command()
async def ping(ctx):
    await ctx.send(embed=discord.Embed(title=f"Latency: `{round(client.latency*100,4)}`ms"))

@client.command(name="leaderboard",aliases=["lb"])
@commands.cooldown(1, 30, commands.BucketType.guild)
async def leaderboard_cmd(ctx):
    global USERNAMES
    start = time.time()
    async with ctx.typing():
        iden,xps,level,joined,ordered = USERNAMES.copy(),[i[1] for i in RAW],[i[2] for i in RAW],[i[3] for i in RAW],[]
        await client.wait_until_ready()
        while len(ordered)<10:
            index = xps.index(max(xps))
            ordered.append([iden[index],xps[index],level[index],joined[index]])
            iden.pop(index)
            xps.pop(index)
            level.pop(index)
            joined.pop(index)
        log(ordered)
        embed = discord.Embed(
            title = "Global Leaderboard",
            colour = discord.Colour.blurple()
        ).set_footer(text=f"Generated in {round(time.time()-start,4)} Seconds. Enhanced Response time from Legacy.")
        for i in ordered[:10]:
            embed.add_field(name=f"{ordered.index(i)+1}) `{i[1]}`\t**Level**: `{i[2]}`\t\t\t\t**{i[0]}**",value=f"Joined in {i[3]}",inline=False)
    await ctx.send(embed=embed)

@client.command(aliases=['sb'])
async def superbroadcast(ctx):
    if ctx.author.id in [591107669180284928,852572302590607361]:
        await ctx.send(
            "Type in What You want to broadcast\n`Type cancel to force end`")
        msg = await client.wait_for('message', check=lambda m:m.author.id == ctx.author.id)
        if msg.content != "" and msg.content != "cancel":
            for i in client.guilds:
              channel = i.system_channel
              await channel.send(
                        f"**Super Broadcast**\n{msg.content}\n\n*By my creator The UKNOWN...*"
                    )
            await ctx.send("Broadcast Successfully Sent!")
        else:
            await ctx.send("`Super Broadcast Cancelled.`")
@client.command(name="level",aliases=["rank"])
async def get_self(ctx):
    if str(ctx.author.id) in USERS:
        user_obj = RAW[USERS.index(str(ctx.author.id))]
        e = discord.Embed(
            title = f"{USERNAMES[USERS.index(str(ctx.author.id))]}'s Profile",
            description = f"**Joined in**: `{user_obj[3]}`\n**Level**: `{user_obj[2]}`\nEXP: `{user_obj[1]}`",
            colour = discord.Colour(0xd81b60)
        ).set_footer(text=f"User ID: {user_obj[0]}")
        await ctx.send(embed=e)
    else:
        await ctx.send("Say **Hi everyone** get your profile")

@client.command()
async def get_raw(ctx):
    if ctx.author.id == 591107669180284928:
        phr = ""
        for i in RAW:
            phr+=f"{i}\n"
            if len(phr)>1000:
                await ctx.send(phr)
                phr = ""

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

@client.command()
async def force_upload(ctx):
    if ctx.author.id == 591107669180284928:
        async with ctx.typing():
            start = time.time()
            p = await ctx.send("Uploading Data Forcefully...")
            await upload_data()
            TO_Next = upload_interval*60
        await p.delete()
        await ctx.send(f"✅ Uploaded Data in `{round(time.time()-start,4)} Seconds`")

@tasks.loop(minutes=upload_interval)
async def upload_loop():
    await upload_data()

async def upload_data():
    global XP_COUNT,USERS,USERNAMES
    if XP_COUNT != {}:
        start = time.time()
        sheet = SPREAD.worksheet("Leveling")
        USERS = sheet.col_values(1)
        cell_updates,new_count = [],0
        for i in XP_COUNT:
            cell_updates.append(gspread.models.Cell(row=USERS.index(i)+1,col=2,value=int(sheet.acell(f"B{USERS.index(i)+1}").value)+XP_COUNT[i]))
        sheet.update_cells(cell_updates)
        log("Uploaded Data!!!")
        RAW = sheet.get_all_values()[1:]
        for i in range(len(RAW)):
            RAW[i][1],RAW[i][2] = int(RAW[i][1]),int(RAW[i][2])
        USERS = [i[0] for i in RAW]
        code_fetch = random.choice(['Alpha','Bravo','Charlie','Delta','Echo','Foxtrot','Golf','Hotel','India','Juliet'])
        log(f"Fetched Information {code_fetch}!!!")
        XP_COUNT = {}
        e = discord.Embed(title="Upload Data",description="\n".join(map(str,cell_updates)),colour=discord.Colour(0x232323)).set_footer(text=f"Uploaded in {time.time()-start} seconds. Fetched information {code_fetch}")
        await client.get_channel(867533836803244042).send(embed=e)
        while True:
            USERNAMES = []
            for i in USERS:
                try:
                    user = await client.fetch_user(i)
                    USERNAMES.append(user.name)
                    log(user)
                except Exception as e:
                    # Execute Self Healing Protocol
                    await self_healing()
                    continue
            break

        log(f"Loaded Usernames\n{USERNAMES}")
        log(f"Loaded USERS:\n{USERNAMES}\nRAW:\n{RAW}")
@tasks.loop(seconds=5)
async def change_p():
    statuses = [f"{len(client.guilds)} Servers","you talk","Growtopia Leveling System",f"{len(USERNAMES)} Players"]
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=random.choice(statuses)))

@change_p.before_loop
@update_cooldown.before_loop
async def check_ready():
    await client.wait_until_ready()

#Run Background tasks
bg_tasks = [update_cooldown,upload_loop,change_p]
for i in bg_tasks:
    i.start()

client.run(os.getenv('token'))
