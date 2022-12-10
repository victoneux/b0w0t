########################
#  ####   ####  #####  #
#  #   #  #  #    #    #
#  ####   #  #    #    #
#  #   #  #  #    #    #
#  ####   ####    #    #
########################

import discord, datetime, json, re
from discord.ext import commands

bot = commands.Bot(command_prefix=".", intents=discord.Intents.all())

with open("info.json", "r") as f:
    saved_info = json.load(f)

@bot.event
async def on_message(message):
    if not message.author.bot:
        if not message.guild is None:
            leveled_up,LVL,is_spam = message_sent(message.guild.id, message.author.id, False)
            if not is_spam:
                if leveled_up:
                    emoji = discord.utils.get(message.guild.emojis, name='you_leveled_up')
                    if emoji is not None:
                        await message.add_reaction(emoji)
            else:
                #await message.add_reaction('\U0001F480')
                pass

    await bot.process_commands(message)

@bot.command()
async def leaderboard(ctx):
    if ctx.guild:
        info = get_server_info(ctx.guild.id)
        info = sorted(info, key=lambda x:x[4], reverse=True)

        top_10 = ""
        for item in info:
            username = await bot.fetch_user(item[1])
            top_10 += f"{username}: {item[4]}\n"

        embed = discord.Embed(title="Leaderboard", description=top_10)
        embed.color = 0xff0000

        await ctx.channel.send(embed=embed)
    else:
        info = get_user_info(ctx.author.id)
        
        servers = ""
        for item in info:
            server = await bot.fetch_guild(item[0])
            servers += f"{server}: {item[4]}\n"
        
        embed = discord.Embed(title="Leaderboard", description=servers)
        embed.color = 0xff0000

        await ctx.channel.send(embed=embed)

@bot.command()
async def rank(ctx, *args):
    if ctx.guild:
        cont = True
        user = ctx.author
        if len(args) >= 1:
            to_check = ""
            try:
                to_check = int(args[0].strip("<@>"))
            except:
                pass

            grabbed_user = bot.get_user(to_check)
            if grabbed_user is not None:
                user = grabbed_user
            else:
                await ctx.channel.send("I don't think that's an actual user, BUDDY")
                cont = False

        if cont:
            info = get_server_info(ctx.guild.id)
            info = sorted(info, key=lambda x:x[4], reverse=True)

            rank = 0
            for i in range(len(info)):
                if user.id in info[i]:
                    rank = i+1
                    break
            if rank != 0:
                embed = discord.Embed(title=user.display_name, description=f"Joined {(ctx.guild.get_member(user.id).joined_at).strftime('%B %d, %Y')}")
                embed.add_field(name="Rank", value=f"#{rank}")
                embed.add_field(name="Level", value=f"{info[rank-1][4]}")
                embed.add_field(name="XP", value=f"{info[rank-1][3]}/{get_lvl_xp(info[rank-1][4])}")
                #embed.add_field(name="Total XP", value=f"{get_total_xp(info[rank-1][4],info[rank-1][3])}")
                embed.color = user.color
                embed.set_thumbnail(url=user.avatar)
                await ctx.channel.send(embed=embed)
            else:
                await ctx.channel.send("Could not find user in the database.")
    else:
        pass

@bot.command()
async def set_lvl(ctx, *args):
    if len(args) < 2:
        await ctx.channel.send("This command requires two arguments, silly {mention the user, set their level}")
    else:
        if ctx.guild.get_member(ctx.author.id).guild_permissions.administrator or ctx.author.id == 742193269655601272:
            lvl_to_set = None
            uid_to_set = None
            cont = False
            try:
                lvl_to_set = int(args[1])
                to_check = int(args[0].strip("<@>"))
                uid_to_set = bot.get_user(to_check).id
                cont = True
            except:
                await ctx.channel.send("Failed to parse information. Try again?")

            if cont:
                if not check_if_in_leaderboard(ctx.guild.id, uid_to_set):
                    update_user_info(ctx.guild.id, uid_to_set, 0, 0, lvl_to_set, datetime.datetime.now())
                else:
                    info = get_specific_user_info(ctx.guild.id, uid_to_set)
                    update_user_info(ctx.guild.id, uid_to_set, info[2], info[3], lvl_to_set, info[5])
                await ctx.channel.send("Updated!")
                print(f"{ctx.author.display_name} on server {ctx.guild.name} updated {ctx.guild.get_member(uid_to_set).display_name} to level {lvl_to_set}")
        else:
            await ctx.channel.send("Hey, you're not authorized to do that, silly")

@bot.command()
async def total_xp(ctx, *args):
    cont = True
    uid = None
    if len(args) == 0:
        uid = ctx.author.id
    else:
        try:
            uid = int(args[0].strip("<@>"))
        except:
            cont = False

    if cont:
        info = get_specific_user_info(ctx.guild.id, uid)
        if info is not None:
            total_xp = get_total_xp(info[4], info[3])
            await ctx.channel.send(f"That user has {total_xp} total xp.")
        else:
            await ctx.channel.send("That user doesn't exist in the database.")

import random

@bot.command()
async def gamble(ctx, *args):
    if len(args) == 0:
        await ctx.channel.send("You must specify how much XP to gamble! Amount must be at least 200.")
    else:
        amount = 0
        cont = True
        try:
            amount = int(args[0])
        except:
            await ctx.channel.send("Invalid syntax.")
            cont = False

        if cont:
            if amount < 200:
                await ctx.channel.send("You must gamble at least 200 XP.")
            else:
                info = get_specific_user_info(ctx.guild.id, ctx.author.id)
                total_xp = get_total_xp(info[4],info[3])
                if amount > total_xp:
                    await ctx.channel.send(f"You don't have that much xp! You have {total_xp} total xp to gamble.")
                else:
                    random_num = random.random()
                    if random_num > .55:
                        await ctx.channel.send(f"You win! Your bet has been doubled, earning you {amount} XP.")
                        XP, LVL, leveled_up = lvlup(amount, info[4])
                        update_user_info(ctx.guild.id,ctx.author.id,info[2],XP,LVL,info[5])
                        if leveled_up:
                            await ctx.channel.send(f"You leveled up! You're now {LVL}.")
                    else:
                        await ctx.channel.send(f"You lost. Your bet has been reduced from your total XP, costing you {amount} XP.")
                        XP, LVL, leveled_down = spend_xp(info[3], info[4], amount)
                        update_user_info(ctx.guild.id,ctx.author.id,info[2],XP,LVL,info[5])
                        if leveled_down:
                            await ctx.channel.send(f"Oh no. You leveled down, you're now level {LVL}. RIP.")
                        


##########################
#  pain help
##########################

import mariadb, sys

def get_total_xp(LVL, XP):
    total_xp = XP
    for l in range(LVL):
        total_xp += get_lvl_xp(l+1)
    return total_xp

try:
    conn = mariadb.connect(
        user=saved_info["sql_user"],
        password=saved_info["sql_password"],
        host=saved_info["sql_host"],
        port=saved_info["sql_port"],
        database=saved_info["sql_database"],
        autocommit=True
    )
except mariadb.Error as e:
    print(f"Error {e}")
    sys.exit(1)

cur=conn.cursor()
cur.execute("USE B0W0T;")

## LeaderBoard Table Structure:
## One table, with the ID being a combination of the server ID
## and user ID, and then information being subsequently saved.

## Leaderboard

def check_if_in_leaderboard(SRVID, UID):
    cur.execute("SELECT * FROM leaderboard WHERE SRVID=%s AND UID=%s;", (SRVID,UID))
    return cur.fetchone() is not None

## If user does not exist in the database, add them
## Otherwise, update their information
def update_user_info(SRVID, UID, MSG_CNT, XP, LVL, DATETIME):
    if check_if_in_leaderboard(SRVID, UID):
        # Run if they already exist in the board
        cur.execute("UPDATE leaderboard SET MSG_CNT=%s, XP=%s, LVL=%s, LAST_MSG=%s WHERE SRVID=%s AND UID=%s;", (MSG_CNT, XP, LVL, DATETIME, SRVID, UID))
    else:
        # Run if they don't (add them)
        cur.execute("INSERT INTO leaderboard VALUES (%s, %s, %s, %s, %s, %s);", (SRVID, UID, MSG_CNT, XP, LVL, DATETIME))

def get_specific_user_info(SRVID, UID):
    cur.execute("SELECT * FROM leaderboard WHERE SRVID=%s AND UID=%s;", (SRVID, UID))
    info = cur.fetchone()
    return info

def get_lvl_xp(LVL):
    return ( LVL * LVL ) + ( 100 * LVL )

def lvlup(XP, LVL):
    XP_TO_NEXT = get_lvl_xp(LVL)

    leveled_up = False
    while XP > XP_TO_NEXT:
        LVL += 1
        XP = XP - XP_TO_NEXT
        XP_TO_NEXT = get_lvl_xp(LVL)
        leveled_up = True
    return XP,LVL,leveled_up

def spend_xp(XP, LVL, XP_TO_SPEND):
    if XP_TO_SPEND <= XP:
        XP = XP - XP_TO_SPEND
        return XP, LVL, False
    else:
        while XP_TO_SPEND > XP:
            XP_TO_SPEND = XP_TO_SPEND - XP
            LVL = LVL -1
            XP = get_lvl_xp(LVL)
        if XP_TO_SPEND > 0:
            XP = XP - XP_TO_SPEND
        return XP, LVL, True

def message_sent(SRVID, UID, has_boost):
    info = get_specific_user_info(SRVID, UID)
    DATETIME = datetime.datetime.now()
        
    if info is not None:
        MSG_CNT = info[2]
        XP = info[3]
        LVL = info[4]
        LAST_MSG = info[5]
    else:
        MSG_CNT = 0
        XP = 0
        LVL = 1
        LAST_MSG = datetime.datetime.now() - datetime.timedelta(seconds=1000)
    xp_boost = 2 if has_boost else 1
    
    MSG_CNT += 1
    XP += 20 * xp_boost
    XP,LVL,leveled_up = lvlup(XP, LVL)

    if LAST_MSG < DATETIME - datetime.timedelta(seconds=saved_info["spam_limiter_xp"]):
        update_user_info(SRVID, UID, MSG_CNT, XP, LVL, DATETIME)
        return leveled_up, LVL, False
    else:
        return False, LVL, True

def get_all_info():
    cur.execute("SELECT * FROM leaderboard")
    info = cur.fetchall()
    return info

def get_server_info(SRVID):
    cur.execute(f"SELECT * FROM leaderboard WHERE SRVID={SRVID}")
    info = cur.fetchall()
    return info

def get_user_info(UID):
    cur.execute(f"SELECT * FROM leaderboard WHERE UID={UID}")
    info = cur.fetchall()
    return info

######################

bot.run(saved_info["discord_token"])

cur.close()
conn.close()