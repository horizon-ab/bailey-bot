import discord
from discord.ext import commands
import os

intents = discord.Intents.default()
intents.message_content = True
token = os.getenv("DISCORD_PUBLIC_KEY")

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event()
async def on_ready():

@bot.event()
async def on_message(message):
    if message.author == client.user:
        return

@bot.command()
async def 

client.run(token)
