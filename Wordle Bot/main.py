import discord
from discord.ext import commands, tasks
from discord import app_commands
import datetime
from dotenv import load_dotenv
import os
from datetime import datetime, date as DateClass
from datetime import datetime

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
wordle_file = "wordlenumber.txt"
wordle_id = os.getenv("WORDLE_ID")
wordle_role_id = os.getenv("WORDLE_ROLE_ID")
guild_id = os.getenv("GUILD_ID")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


#read and write to wordlenumber file
def read_wordle_file():
    if not os.path.exists(wordle_file):
        return None
    with open(wordle_file, "r") as f:
        try:
            return int(f.read().strip())
        except:
            return None


def write_wordle_file(number: int):
    with open(wordle_file, "w") as f:
        f.write(str(number))


def get_wordle_number(date: datetime.date):
    og_wordle = DateClass(2021, 6, 19)
    return (date - og_wordle).days

#events
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"{bot.user} is online!")
    
#slash command
@bot.tree.command(name="wordlenumber", description="x-days from OG Wordle")
@app_commands.describe(user_date="Enter date in YYYY-MM-DD format")
async def wordlenumber(interaction: discord.Interaction, user_date: str):
    try:
        parsed_date = datetime.strptime(user_date, "%Y-%m-%d").date()
        og_wordle = DateClass(2021, 6, 19)
        days_diff = (parsed_date - og_wordle).days
        await interaction.response.send_message(f"{days_diff} is the Wordle number for the date provided")
    except ValueError:
        await interaction.response.send_message("Invalid date or format :( Use YYYY-MM-DD", ephemeral=True)

#fun little snippet that keeps track of the gaffes consecutive messages and gives role if someone has done the wordle
#{channel_id: {"message": str, "count": int}}
streaks = {}

@bot.event
async def on_message(message):
    # detect Wordle bots /share message
    if message.type == discord.MessageType.chat_input_command and message.author.id == wordle_id:
        print("Wordle Command was executed")
        guild = message.guild
        role = guild.get_role(wordle_role_id)
        user = message.interaction.user if message.interaction else None
        if user is None:
            return

        #get todays Wordle number
        today_num = get_wordle_number(datetime.now().date())
        stored_num = read_wordle_file()

        if stored_num is None:
            write_wordle_file(today_num)
            stored_num = today_num

        if today_num != stored_num:
            #wipe everyones role first
            await message.channel.send(f"**{user.display_name}** was the first to complete todays wordle!")
            for member in role.members:
                try:
                    await member.remove_roles(role)
                    await message.channel.send(f"Removed role from **{member.display_name}**")
                    print(f"Removed role from **{member.display_name}**")
                except Exception as e:
                    print(f"Failed removing role from **{member.display_name}**: {e}")

            #give the role only to the triggering user
            await user.add_roles(role)
            await message.channel.send(
                f"**{user.display_name}** has unlocked today’s Wordle role (#{today_num})! 🎉,")

            #update the file with the new number
            write_wordle_file(today_num)

        else:
            #normal behavior gives role if they dont already have it
            if role not in user.roles:
                await user.add_roles(role)
                await message.channel.send(
                    f"**{user.display_name}** You have been given the Wordle_Completed Role."
                    f" Go chat in the finished_wordle channel!",ephemeral=True
                )
            else:
                await message.channel.send(f"{user.display_name} You already have the role you sly fox.")

    if message.author.bot:
        return

    channel_id = message.channel.id
    content = message.content.strip()

    #check if the current channel already has a streak
    if channel_id not in streaks:
        streaks[channel_id] = {"message": content, "count": 1}
    else:
        if streaks[channel_id]["message"] == content:
            streaks[channel_id]["count"] += 1
        else:
            #streak ended, gives the number of the streak and the name of the person who broke the streak so we can shame them
            if streaks[channel_id]['count'] > 1:
                await message.channel.send(f"Streak count ended at {streaks[channel_id]['count']} by {message.author}")
                print(f"Streak in channel {message.channel.name} ended at {streaks[channel_id]['count']}")
            streaks[channel_id] = {"message": content, "count": 1}

    await bot.process_commands(message)
    
bot.run(TOKEN)