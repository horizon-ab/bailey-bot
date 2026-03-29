# bot.py

import discord
from discord.ext import commands
import os

import model

intents = discord.Intents.default()
intents.message_content = True
token = os.getenv("DISCORD_PUBLIC_KEY")

bot = commands.Bot(command_prefix='/', intents=intents)

message_threshold = 3
confidence_auto = 0.9
confidence_manual = 0.7


@bot.event()
async def on_ready():
    pass

@bot.event()
async def on_message(message):
    if message.author == client.user:
        return



client.run(token)
