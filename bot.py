# bot.py

import discord
from discord.ext import commands
import os

from model.inference import load_model, predict

class BaileyBot(commands.Bot):
    def __init__(self, run_dir, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_dir = run_dir

        self.model = None
        self.tokenizer = None
        self.device = None

    async def setup_hook(self):
        self.model, self.tokenizer, self.device = load_model(self.run_dir)
        print(f"Successfully loaded model onto {self.device}")

intents = discord.Intents.default()
intents.message_content = True
token = os.getenv("DISCORD_TOKEN")

message_threshold = 3
confidence_auto = 0.9
confidence_manual = 0.7

RUN_DIR = "./model/outputs/run_20260331-203654"

bot = BaileyBot(run_dir=RUN_DIR, command_prefix='/', intents=intents)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    score = predict(message.content, bot.model, bot.tokenizer, bot.device)

    if score > confidence_auto:
        await message.channel.send(f"High Likelihood of Scam: {score:.2f}")
    elif score > confidence_manual:
        await message.channel.send(f"Medium Likelihood of Scam: {score:.2f}")

    await bot.process_commands(message)



bot.run(token)
