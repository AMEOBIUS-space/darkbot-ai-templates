#!/usr/bin/env python3
"""Discord Bot Template — production-ready with slash commands, moderation, music queue."""
import asyncio, os, logging
import discord
from discord.ext import commands
from discord import app_commands

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("DISCORD_TOKEN", "")
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

WELCOME_CHANNEL = None
MUSIC_QUEUE = {}

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"Sync error: {e}")

@bot.event
async def on_member_join(member):
    if WELCOME_CHANNEL:
        ch = bot.get_channel(WELCOME_CHANNEL)
        await ch.send(f"Welcome {member.mention} to {member.guild.name}! 🎉")

# Slash commands
@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="userinfo", description="Get user info")
async def userinfo(interaction: discord.Interaction, member: discord.Member = None):
    member = member or interaction.user
    embed = discord.Embed(title=f"{member.name}#{member.discriminator}", color=0x58a6ff)
    embed.add_field(name="ID", value=member.id)
    embed.add_field(name="Joined", value=member.joined_at.strftime("%Y-%m-%d"))
    embed.add_field(name="Roles", value=len(member.roles))
    embed.set_thumbnail(url=member.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="purge", description="Delete messages (mod only)")
@app_commands.describe(count="Number of messages to delete")
async def purge(interaction: discord.Interaction, count: int):
    if not interaction.user.guild_permissions.manage_messages:
        return await interaction.response.send_message("No permission!", ephemeral=True)
    deleted = await interaction.channel.purge(limit=count)
    await interaction.response.send_message(f"Deleted {len(deleted)} messages", ephemeral=True)

@bot.tree.command(name="play", description="Add song to queue (template)")
async def play(interaction: discord.Interaction, query: str):
    guild_id = interaction.guild_id
    if guild_id not in MUSIC_QUEUE:
        MUSIC_QUEUE[guild_id] = []
    MUSIC_QUEUE[guild_id].append(query)
    await interaction.response.send_message(f"Added to queue: {query} (position {len(MUSIC_QUEUE[guild_id])})")

@bot.tree.command(name="queue", description="Show music queue")
async def queue(interaction: discord.Interaction):
    q = MUSIC_QUEUE.get(interaction.guild_id, [])
    if not q:
        return await interaction.response.send_message("Queue is empty")
    text = "\n".join(f"{i+1}. {song}" for i, song in enumerate(q[:10]))
    await interaction.response.send_message(f"**Queue:**\n{text}")

@bot.tree.command(name="poll", description="Create a poll")
async def poll(interaction: discord.Interaction, question: str, *options: str):
    if len(options) < 2 or len(options) > 10:
        return await interaction.response.send_message("Provide 2-10 options")
    emojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    desc = "\n".join(f"{emojis[i]} {opt}" for i, opt in enumerate(options))
    embed = discord.Embed(title=f"📊 {question}", description=desc, color=0x7ee787)
    await interaction.response.send_message(embed=embed)
    msg = await interaction.original_response()
    for i in range(len(options)):
        await msg.add_reaction(emojis[i])

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
