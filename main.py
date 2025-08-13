import discord
from discord.ext import commands
from discord import app_commands
import logging
from dotenv import load_dotenv
import os
from death_causes import death_causes
import random
import asyncio

load_dotenv()

token = os.getenv('DISCORD_TOKEN')
#guild_id = int(os.getenv("GUILD_ID"))
channel_id = int(os.getenv("CHANNEL_ID"))
safe_name = "Alive"
dead_name = "Perished"

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.guilds = True

game_started = False  # No one has played yet
has_greeted = False
all_dead = False
survival_days = {}

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def ensure_roles_exist(guild: discord.Guild):
    alive_role = discord.utils.get(guild.roles, name=safe_name)
    dead_role = discord.utils.get(guild.roles, name=dead_name)

    if alive_role is None:
        alive_role = await guild.create_role(
            name=safe_name,
            colour=discord.Colour.teal()  # Bright turquoise
        )
        print(f"✅ Created role: {alive_role} with teal color")

    if dead_role is None:
        dead_role = await guild.create_role(
            name=dead_name,
            colour=discord.Colour.dark_red()  # Dark red
        )
        print(f"✅ Created role: {dead_role} with dark red color")

    return alive_role, dead_role

@bot.tree.command(name="playgame", description="Join the apocalypse!")
async def playgame(interaction: discord.Interaction):
    global game_started
    game_started = True
    all_dead = False

    try:
        print("➡️ /playgame triggered")
        guild = interaction.guild
        member = interaction.user

        alive_role = discord.utils.get(guild.roles, name="Alive")
        if alive_role is None:
            print("🔧 Alive role not found, creating...")
            alive_role = await guild.create_role(name="Alive", colour=discord.Colour.teal())
            await interaction.response.send_message("🛠️ Created 'Alive' role. Try the command again!")
            return
        else:
            print("✅ Alive role exists")

        if alive_role not in member.roles:
            print("🧠 Assigning Alive role to user...")
            await member.add_roles(alive_role)
            await interaction.response.send_message(f"✅ {member.display_name} has joined the apocalypse as an **Alive** player!")
        else:
            print("⚠️ User already has Alive role")
            await interaction.response.send_message("⚠️ You're already marked as **Alive**!")

    except Exception as e:
        print(f"❌ Error in /playgame: {e}")
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message("❌ Something went wrong!", ephemeral=True)
            except:
                pass

@bot.event
async def schedule_daily_death(guild):
    await bot.wait_until_ready()
    global has_greeted, all_dead

    channel = discord.utils.get(guild.text_channels, name="apocalypse-log")

    # If channel doesn't exist, create it
    if channel is None:
        try:
            channel = await guild.create_text_channel("apocalypse-log")
            print(f"📢 Created 'apocalypse-log' channel in {guild.name}")
        except Exception as e:
            print(f"❌ Failed to create channel in {guild.name}: {e}")
            return

    while True:
        try:
            alive_role, dead_role = await ensure_roles_exist(guild)
            alive_members = [member for member in guild.members if alive_role in member.roles and not member.bot]

            for member in alive_members:
                if alive_role in member.roles and not member.bot:
                    uid = member.id
                    survival_days[uid] = survival_days.get(uid, 0) + 1

            if alive_members:
                victim = random.choice(alive_members)
                cause = random.choice(death_causes)

                await victim.remove_roles(alive_role)
                await victim.add_roles(dead_role)

                days = survival_days.get(victim.id, 0)
                await channel.send(f"💀 **{victim.display_name}** has fallen after **{days} day(s)**: {cause}")
            else:
                if not game_started:
                    if not has_greeted:
                        await channel.send("Are you ready to join the apocalypse? Type `/playgame` to participate and `/leaderboard` to check the stats.")
                        has_greeted = True
                else:
                    if not all_dead:
                        await channel.send("Everyone is dead. The zombies have taken over. 🧟")
                        all_dead = True
        except Exception as e:
            print(f"❌ Error in schedule_daily_death loop: {e}")
            try:
                await channel.send("⚠️ Error in daily death loop.")
            except:
                pass

        await asyncio.sleep(20)  # wait 24 hours, put 86400


@bot.tree.command(name="leaderboard", description="See who survived the longest!")
async def leaderboard(interaction: discord.Interaction):
    if not survival_days:
        await interaction.response.send_message("No survival stats yet! Type `/playgame` to join in.")
        return

    # Sort users by days survived
    sorted_scores = sorted(survival_days.items(), key=lambda x: x[1], reverse=True)
    top_list = []

    for i, (uid, days) in enumerate(sorted_scores[:10], start=1):
        member = interaction.guild.get_member(uid)
        name = member.display_name if member else f"User {uid}"
        top_list.append(f"**{i}. {name} — {days} day(s)**")

    result = "\n".join(top_list)
    await interaction.response.send_message(f"🏆 **Zombie Survival Leaderboard**\n{result}")


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

    await bot.change_presence(
        activity=discord.Game(name="snacking on brains 🧠")
    )

    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} commands globally")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

    for guild in bot.guilds:
        bot.loop.create_task(schedule_daily_death(guild))

bot.run(token, log_handler=handler, log_level=logging.DEBUG)