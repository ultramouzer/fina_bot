# bot.py
import os
import random
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import pso2
import asyncio
import psycopg2

TOKEN = os.environ['DISCORD_TOKEN']
GUILD = os.environ['GUILD_NAME']
HOST  = os.environ['DATABASE_URL']
DB    = os.environ['DB_NAME']
USER  = os.environ['USER_NAME']
PASS  = os.environ['PASSWORD']
# guild is another name for server

bot = commands.Bot(command_prefix=('fina ', 'Fina '))  # this line is why some bots need ! for commands. 2 prefixes allowed.

character_list = []

@bot.event
async def on_ready():
    # prints to terminal
    db = psycopg2.connect(HOST, sslmode='require')
    #    host = HOST,
    #    database = DB,
    #    user = USER,
    #    password = PASS
    #)
    cursor = db.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS character_list(
        character_name text,
        user_name text,
        user_id bigint
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quest(
        quest_name text,
        diff text,
        clear text,
        character_name text,
        user_id bigint,
        quest_id SERIAL PRIMARY KEY
        )
    ''')#FOREIGN KEY(user_id) REFERENCES character_list(user_id)
    db.commit()
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(
        f'{bot.user} is connected to the following server:\n'
        f'{guild.name}(id: {guild.id})'
    )
    members = '\n - '.join([member.name for member in guild.members])
    print(f'Server Members:\n - {members}')

    cursor.execute("SELECT * FROM character_list")
    db_char_list = cursor.fetchall()

    for x in db_char_list:
        character = pso2.Character(x[0], x[1], x[2])
        #add to character.quest_list here
        cursor.execute("SELECT * FROM quest WHERE character_name=%s AND user_id=%s", (x[0], x[2]))
        char_quest_list = cursor.fetchall()

        for y in char_quest_list:
            addThisQuest = pso2.Quest(y[0], y[1], y[2], y[3], y[5])
            #quest_name, diff, clear, character_name, quest_id
            character.quest_list.add(addThisQuest)

        character_list.append(character)
    
    cursor.close()
    db.close()

@bot.event  # doesn't need ! prefix
async def on_message(message):
    # THIS FOLLOWING LINE VERY IMPORTANT SO BOT DOESN'T RECUR ITSELF
    if message.author == bot.user:
        return

    if message.content == '69':
        response = 'Nice'
        await message.channel.send(response)

    if message.content == '420':
        response = 'lmao weed'
        await message.channel.send(response)
    await bot.process_commands(message)  # this line needed or commands won't work anymore


@bot.command(name='hentai')
async def hentai(ctx):
    response = 'ask ultramouzer for it'
    await ctx.send(response)


@bot.command(name='addchar', help='fina addchar {character name}, makes a new character')
async def char(ctx, *, name):
    #query db and look for dupes
    #not yet implemented
    
    myChar = pso2.Character(name, ctx.author.name, ctx.author.id)
    character_list.append(myChar)

    db = psycopg2.connect(HOST, sslmode='require')
    #    host = HOST,
    #    database = DB,
    #    user = USER,
    #    password = PASS
    #)
    #insert character into database
    cursor = db.cursor()
    cursor.execute('INSERT INTO character_list(character_name, user_name, user_id) VALUES (%s, %s, %s)', (myChar.name, myChar.user_name, myChar.user_id))
    db.commit()

    response = 'Character added, User: ' + ctx.author.name + ', character name: ' + myChar.name
    await ctx.send(response)

    cursor.close()
    db.close()

@char.error
async def char_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('missing character name. type fina help addchar for detailed usage.')
    

@bot.command(name='delchar', help='fina delchar {character name}, deletes an existing character')
async def delchar(ctx, *, name):

    for x in character_list:#finds the user's character
        if x.user_id == ctx.author.id and x.name == name:
            character = x
            break
    if character == None:#character not found
        response = 'character not found'
        await ctx.send(response)
        return
    
    response = 'Are you sure you want to delete ' + character.name +'? Type y or n.'
    await ctx.send(response)
    print("please do something before the check")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=10.0)
    except asyncio.TimeoutError:
        return

    if msg.content == 'y' or msg.content == 'Y':
        await ctx.send(character.name + ' deleted')
        #do deletion here
        db = psycopg2.connect(HOST, sslmode='require')
    #    host = HOST,
    #    database = DB,
    #    user = USER,
    #    password = PASS
    #)
        cursor = db.cursor()
        cursor.execute('DELETE FROM character_list WHERE character_name=%s AND user_id=%s', (character.name, character.user_id,))
        cursor.execute('DELETE FROM quest WHERE character_name=%s AND user_id=%s', (character.name, character.user_id,))
        db.commit()

        character_list.remove(character)
    elif msg.content == 'n' or msg.content == 'N':
        await ctx.send('character not deleted')
    else:
        await ctx.send('invalid argument')

    cursor.close()
    db.close()

@delchar.error
async def delchar_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('missing character name. type fina help delchar for detailed usage.')

@bot.command(name='addquest', help='fina addquest {character name} {quest name} {difficulty: XH, SH, VH, H, N or numeric level. defaults to SH} {rank: S, A, B, C. defaults to A}.\n please enter exact quest name with punctuation to ensure success. \n put quest name in quotations if containing spaces.')
async def add(ctx, char_name, quest_name, diff='SH', clear='A'):
    response = ''
    character = None
    
    for x in character_list:#finds the user's character
        if x.user_id == ctx.author.id and x.name == char_name:
            character = x
            break
    if character == None:#character not found
        response = 'character not found'
        await ctx.send(response)
        return

    #check validity of difficulty, convert to alphabetical format if needed
    if diff.isnumeric() == True:
        tempDiff = int(diff)
        tempDiff = tempDiff // 10
        diff = switchDiff(tempDiff)
        if tempDiff < 2:
            diff = 'N'
        elif tempDiff < 4:
            diff = 'H'
        elif tempDiff == 4:
            diff = 'VH'
        elif tempDiff < 6:
            diff = 'SH'
        elif tempDiff >= 7:
            diff = 'XH'
        else:
            response = 'Invalid difficulty. \n type fina help addquest for detailed usage.'
            await ctx.send(response)
            return
    
    if diff == 'n':
        diff = 'N'
    elif diff == 'h':
        diff = 'H'
    elif diff == 'vh':
        diff = 'VH'
    elif diff == 'sh':
        diff = 'SH'
    elif diff == 'EH' or diff == 'EXH' or diff == 'eh' or diff == 'exh':#3 ways of shortening "extremely hard"
        diff = 'XH'

    if diff != 'N' and diff != 'H' and diff != 'VH' and diff != 'SH' and diff != 'XH':
        response = 'Invalid difficulty. \n type fina help addquest for detailed usage.'
        await ctx.send(response)
        return

    if character == None:
        response = 'character not found'
        await ctx.send(response)
        return

    if clear == 'c':
        clear = 'C'
    elif clear == 'b':
        clear = 'B'
    elif clear == 'a':
        clear = 'A'
    elif clear == 's':
        clear = 'S'

    #check validity of clear
    if clear != 'C' and clear != 'B' and clear != 'A' and clear != 'S':
        response = 'Invalid clear rank. \n type fina help addquest for detailed usage.'
        await ctx.send(response)
        return
    #add quest into database
    db = psycopg2.connect(HOST, sslmode='require')
    #    host = HOST,
    #    database = DB,
    #    user = USER,
    #    password = PASS
    #)
    cursor = db.cursor()
    cursor.execute('INSERT INTO quest(quest_name, diff, clear, character_name, user_id, quest_id) VALUES (%s, %s, %s, %s, %s, DEFAULT)', (quest_name, diff, clear, character.name, ctx.author.id))
    db.commit()

    quest_id = cursor.lastrowid
    addThisQuest = pso2.Quest(quest_name, diff, clear, character.name, quest_id)
    character.quest_list.add(addThisQuest)

    response = 'added ' + quest_name + ' ' + diff + ' rank: ' + clear + ' to ' + character.name + '\'s order list'
    await ctx.send(response)

    cursor.close()
    db.close()

@add.error
async def add_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('missing required arguments name. type fina help addquest for detailed usage.')

#deletes a client order
@bot.command(name='delquest', help='fina delquest {character name} {client order index}. \n deletes a client order from character\'s list. \n use the !list command to view your list')
async def delete(ctx, name, idx=None):
    response = ''
    character = None

    for x in character_list:#finds the user's character
        if x.user_id == ctx.author.id and x.name == name:
            character = x
            break
    if character == None:#character not found
        response = 'character not found'
        await ctx.send(response)
        return
    # check validity of index
    if idx.isnumeric() == False:
        response = 'index not a number or is missing. \n type fina help list for detailed usage.'
        await ctx.send(response)
        return
    idx = int(idx) - 1
    removedQuest = character.quest_list.remove_idx(idx)

    #test the quest_id if its retrieving the correct values
    #change remove via idx to remove via quest id?
    db = psycopg2.connect(HOST, sslmode='require')
    #    host = HOST,
    #    database = DB,
    #    user = USER,
    #    password = PASS
    #)
    #remove quest from database
    cursor = db.cursor()
    print(removedQuest.quest_id)
    cursor.execute('DELETE FROM quest WHERE quest_id = %s', (removedQuest.quest_id,))
    db.commit()

    response = 'deleted ' + removedQuest.name
    await ctx.send(response)

    cursor.close()
    db.close()

@delete.error
async def delete_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('missing character name. type fina help delquest for detailed usage.')


@bot.command(name='list', help='fina list {character name}. displays list of orders')
async def orders(ctx, name):
    response = ''
    character = None
    for x in character_list:#finds the user's character
        if x.user_id == ctx.author.id and x.name == name:
            character = x
            break
    if character == None:#character not found
        response = 'character not found'
        await ctx.send(response)
        return

    response = character.quest_list.listToString(character.name)
    await ctx.send(response)

@orders.error
async def orders_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('missing character name. type fina help list for detailed usage.')

@bot.command(name='chars', help='fina chars. displays the user\'s characters')
async def char(ctx):
    response = ctx.author.name + ' \'s characters:\n'
    for x in character_list:  # finds all of the user's characters
        if x.user_id == ctx.author.id:
            response += x.name + '\n'
    await ctx.send(response)

@bot.command(name='match', help='fina match {your character\'s name}. match client orders with all other characters')
async def match(ctx, name):
    response = ''
    character = None
    
    for x in character_list:#finds the user's character
        if x.user_id == ctx.author.id and x.name == name:
            character = x
            break
            
    if character == None:
        response = 'character not found'
        await ctx.send(response)
        return
    
    for x in character_list:#matches with every other character
        if x.user_id != ctx.author.id:
            response += 'user: ' + x.user_name + ', character name: ' + x.name + '\n quests:\n' + pso2.Character.compare_char_loose(character, x)
    await ctx.send(response)

@match.error
async def match_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('missing character name. type fina help match for detailed usage.')

@bot.command(name='matchuser', help='fina matchuser {your character\'s name} {@ another user}. match client orders with characters of that user')
async def matchuser(ctx, name, *, user: discord.User):
    response = ''
    character = None
    
    for x in character_list:#finds the user's character
        if x.user_id == ctx.author.id and x.name == name:
            character = x
            break
            
    if character == None:
        response = 'character not found'
        await ctx.send(response)
        return

    db = psycopg2.connect(HOST, sslmode='require')
    #    host = HOST,
    #    database = DB,
    #    user = USER,
    #    password = PASS
    #)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM character_list WHERE user_id=%s", (user.id,))
    fetched_char_list = cursor.fetchall()
    user_char_list = []

    #make a list of the desired user's characters
    for x in fetched_char_list:
        character2 = pso2.Character(x[0], x[1], x[2])
        #add to character.quest_list here
        cursor.execute("SELECT * FROM quest WHERE character_name=%s AND user_id=%s", (x[0], x[2]))
        char_quest_list = cursor.fetchall()

        for y in char_quest_list:
            addThisQuest = pso2.Quest(y[0], y[1], y[2], y[3], y[5])
            #quest_name, diff, clear, character_name, quest_id
            character2.quest_list.add(addThisQuest)
        user_char_list.append(character2)

    for x in user_char_list:#matches with every other character
        if x.user_id != ctx.author.id:
            response += 'user: ' + x.user_name + ', character name: ' + x.name + '\nquests:\n' + pso2.Character.compare_char_loose(character, x)

    await ctx.send(response)

    cursor.close()
    db.close()

@matchuser.error
async def matchuser_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('missing required argument(s). type fina help matchuser for detailed usage.')


bot.run(TOKEN)