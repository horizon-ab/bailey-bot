# bot.py

import discord
import os
import asyncio
import json
import shutil
from discord.ext import commands
from dotenv import load_dotenv

from model.inference import load_model, predict
from utils import ServerConfig

class BaileyBot(commands.Bot):
    def __init__(self, run_dir, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_dir = run_dir
        self.configs = {}

        self.model = None
        self.tokenizer = None
        self.device = None

    async def setup_hook(self):
        self.model, self.tokenizer, self.device = load_model(self.run_dir)
        print(f"Successfully loaded model onto {self.device}")

        if os.path.exists("config.json"):
            with open("config.json", "r") as file:
                json_data = json.load(file)
                for guild_id, settings in json_data.items():
                    gid = int(guild_id)
                    self.configs[gid] = ServerConfig.from_dict(gid, settings)
                print("Loaded existing configuration from disk")

        # self.tree.copy_global_to(guild=guild_obj)
        # await self.tree.sync(guild=guild_obj)
        # print(f"Successfully synced commands to guild {SAMPLE_GUILD_ID}")


    def get_config(self, guild_id):
        if guild_id not in self.configs:
            self.configs[guild_id] = ServerConfig(guild_id)
        return self.configs[guild_id]

    def save_configs(self):

        if os.path.exists("config.json"):
            shutil.copy("config.json", "config.json.bak")

        data = {
            str(guild_id): config.to_dict()
            for guild_id, config in self.configs.items()
        }

        with open("config.json", "w") as file:
            json.dump(data, file, indent=4)
        print("Configuration saved to disk.")

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

token = os.getenv("DISCORD_TOKEN")

RUN_DIR = "./model/outputs/run_20260331-213039"

bot = BaileyBot(run_dir=RUN_DIR, command_prefix='$', intents=intents)

# Events

@bot.event
async def on_message(message):
    if message.author == bot.user or message.guild is None:
        return

    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
        return

    config = bot.get_config(message.guild.id)

    if not config.is_active:
        return

    if config.monitor_channels and message.channel.id not in config.monitor_channels:
        return

    score = await asyncio.to_thread(
        predict,
        message.content,
        bot.model,
        bot.tokenizer,
        bot.device
    )

    log_channel = bot.get_channel(config.log_channel_id)

    if score > config.confidence_auto:
        if not log_channel:
            await message.channel.send(f"Message: {message.content}\nHigh Likelihood of Scam: {score:.2f}\nNOTE: Please set up a log_channel with the command `/set log <channel>`")
            return            

        await log_channel.send(f"Message: {message.content}\nHigh Likelihood of Scam: {score:.2f}")
    elif score > config.confidence_manual:
        if not log_channel:
            await message.channel.send(f"Message: {message.content}\nMedium Likelihood of Scam: {score:.2f}\nNOTE: Please set up a log_channel with the command `/set log <channel>`")
            return            
        await log_channel.send(f"Message: {message.content}\nMedium Likelihood of Scam: {score:.2f}")

    # await bot.process_commands(message)

@bot.event
async def on_ready():
    print("Bailey Bot is ready!")

# Commands

@bot.group(invoke_without_command=True)
async def set(ctx):
    pass

@set.command(name="active")
async def set_active(ctx, value: bool):
    config = bot.get_config(ctx.guild.id)
    config.is_active = value
    
    status = "enabled" if value else "disabled"
    await ctx.send(f"Monitoring is now {status}")
    bot.save_configs()

@set.command(name="test")
async def set_test(ctx, value: bool):
    config = bot.get_config(ctx.guild.id)
    config.is_testing = value
    
    status = "enabled" if value else "disabled"
    await ctx.send(f"Testing is now {status}")
    bot.save_configs()

@set.command(name="auto")
async def set_auto(ctx, value: float):
    config = bot.get_config(ctx.guild.id)

    if value > 1.0 or value < 0.0:
        await ctx.send(f"Automatic confidence must be between 0.0 and 1.0")
        return

    config.confidence_auto = value
    await ctx.send(f"Automatic confidence is now {value:.2f}")

    # Manual confidence must be less than or equal to that of auto confidence
    if (config.confidence_manual > value):
        config.confidence_manual = value 
        await ctx.send(f"Manual confidence is now {value:.2f}")
    bot.save_configs()

@set.command(name="manual")
async def set_manual(ctx, value: float):
    config = bot.get_config(ctx.guild.id)

    if value > 1.0 or value < 0.0:
        await ctx.send(f"Manual confidence must be between 0.0 and 1.0")
        return

    config.confidence_manual = value
    await ctx.send(f"Manual confidence is now {value:.2f}")

    # Auto confidence must be greater than or equal to that of manual confidence
    if (config.confidence_auto < value):
        config.confidence_auto = value 
        await ctx.send(f"Automatic confidence is now {value:.2f}")
    bot.save_configs()

@set.command(name="message_threshold")
async def set_message_threshold(ctx, value: int):
    config = bot.get_config(ctx.guild.id)

    config.message_threshold = value
    await ctx.send(f"Message threshold is now {value}")
    bot.save_configs()

@set.command(name="log")
async def set_log(ctx, channel: discord.TextChannel):
    config = bot.get_config(ctx.guild.id)

    if channel.id == config.log_channel_id:
        await ctx.send(f"Channel {channel.name} is already the log channel!")
        return

    config.log_channel_id = channel.id
    await ctx.send(f"Channel {channel.name} is now the log channel")
    bot.save_configs()


@bot.group(invoke_without_command=True)
async def add(ctx):
    pass

@add.command(name="monitor")
async def add_monitor(ctx, channel: discord.TextChannel):
    config = bot.get_config(ctx.guild.id)

    if channel.id in config.monitor_channels:
        await ctx.send(f"Channel {channel.name} is already in monitoring list!")
        return

    config.monitor_channels.append(channel.id)
    await ctx.send(f"Channel {channel.name} has been added to monitoring list")
    bot.save_configs()

@bot.group(invoke_without_command=True)
async def remove(ctx):
    pass

@remove.command(name="monitor")
async def remove_monitor(ctx, channel: discord.TextChannel):
    config = bot.get_config(ctx.guild.id)

    if channel.id not in config.monitor_channels:
        await ctx.send(f"Channel {channel.name} not in monitoring list!")
        return

    config.monitor_channels.remove(channel.id)
    await ctx.send(f"Channel {channel.name} removed from monitoring list")
    bot.save_configs()

bot.run(token)
