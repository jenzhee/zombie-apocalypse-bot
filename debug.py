import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("GUILD_ID"))

intents = discord.Intents.default()
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🔁 Synced {len(synced)} command(s) to GUILD {GUILD_ID}")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")

@bot.tree.command(name="playgame", description="debug ver", guild=discord.Object(id=GUILD_ID))
async def playgame(interaction: discord.Interaction):
    try:
        guild = interaction.guild
        member = interaction.user

        alive_role = discord.utils.get(guild.roles, name="Alive")
        if alive_role is None:
            alive_role = await guild.create_role(name="Alive", colour=discord.Colour.teal())
            await interaction.response.send_message("🛠️ Created 'Alive' role. Try the command again!", ephemeral=True)
            return

        if alive_role not in member.roles:
            await member.add_roles(alive_role)
            await interaction.response.send_message(f"✅ {member.display_name} has joined the apocalypse as **Alive**!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ You're already marked as Alive!", ephemeral=True)

    except Exception as e:
        print(f"❌ Error in /playgame: {e}")
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ Something went wrong!", ephemeral=True)
        except:
            pass


bot.run(TOKEN)
