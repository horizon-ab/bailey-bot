# bot.py

import discord
import os
import asyncio
import json
import shutil
from discord.ext import commands
from discord import utils
from dotenv import load_dotenv

from model.inference import load_model, predict
from utils import ServerConfig, ScamReviewView

NEW_MEMBER_TIME = 86400 * 3 # 3 days

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
intents.members = True
intents.message_content = True

token = os.getenv("DISCORD_TOKEN")

RUN_DIR = "./model/outputs/run_20260331-213039"

bot = BaileyBot(run_dir=RUN_DIR, command_prefix='$', intents=intents)
bot.remove_command('help')

# Judgement

def ping_roles(config, msg):

    roles_text = ""
    for rid in config.monitor_roles:
        role = msg.guild.get_role(rid)
        if role:
            roles_text += f"{role.mention} "

    return roles_text

# Displays during test mode
async def warning(bot, message, score):

    config = bot.get_config(message.guild.id) 

    level = "High" if score > config.confidence_auto else "Medium"
    log_channel = bot.get_channel(config.log_channel_id)

    target_channel = log_channel if log_channel else message.channel
    warning_text = f"Message: {message.content}\nWarning: {level} Likelihood of Scam: {score:.2f}"
    if target_channel != log_channel:
        warning_text += "\nNOTE: Please set up a log channel with the command `$set log <channel>`"

    warning_text += f"\n{ping_roles(config, message)}"

    await target_channel.send(warning_text)

async def judgement(bot, message, score):

    config = bot.get_config(message.guild.id)
    log_channel = bot.get_channel(config.log_channel_id)

    if score > config.confidence_auto:
        try:
            await message.author.ban(delete_message_seconds=259200,
                                     reason=f"Bailey-Bot Autoban: Score {score:.2f} - No sale/scamming"
                                    )
            log_text = f"Message: {message.content}\nHigh Likelihood of Scam: {score:.2f}\nBan has been enforced on user {message.author.name}\n"

        except discord.Forbidden:
            log_text = f"Message: {message.content}\nHigh Likelihood of Scam: {score:.2f}\nBan was attempted, but permissions were lacking to do so."  
        except discord.HTTPException:
            log_text = f"Message: {message.content}\nHigh Likelihood of Scam: {score:.2f}\nBan was attempted, but failed."  

        target = log_channel if log_channel else message.channel
        if target != log_channel:
            log_text += "\nNOTE: Please set up a log channel with the command `$set log <channel>`"

        log_text += f"\n{ping_roles(config, message)}"
           
        await target.send(log_text)

    elif score > config.confidence_manual:
        view = ScamReviewView(bot, message, score)
        target = log_channel if log_channel else message.channel

        log_text = f"Manual Review Needed\nUser: {message.author.name}\nScore: {score:.2f}\nMessage: {message.content}"

        if target != log_channel:
            log_text += "\nNOTE: Please set up a log channel with the command `$set log <channel>`"

        log_text += f"\n{ping_roles(config, message)}"

        await target.send(
                content=log_text,
                view=view
                )

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

    if config.new_only and (utils.utcnow() - message.author.joined_at).total_seconds() > NEW_MEMBER_TIME:
        return

    score = await asyncio.to_thread(
        predict,
        message.content,
        bot.model,
        bot.tokenizer,
        bot.device
    )

    log_channel = bot.get_channel(config.log_channel_id)

    # Score is past the minimum threshold
    if score > config.confidence_manual:
        if config.is_testing:
            await warning(bot, message, score)
        else:
            await judgement(bot, message, score)


@bot.event
async def on_ready():
    print("Bailey Bot is ready!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: `{error.param.name}`.\nUsage: `{ctx.prefix}{ctx.command.qualified_name} <{error.param.name}>`")

    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Bad argument found. Check your formatting!")

    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have the required permissions to use this command!")

    else:
        print(f"Unhandled Error: {error}")

# Commands

@bot.check
async def global_check(ctx):
    config = bot.get_config(ctx.guild.id)

    # Bailey admin powers
    if await bot.is_owner(ctx.author):
        return True

    if ctx.command.name == "help":
        return True

    has_role = any(role.id in config.monitor_roles for role in ctx.author.roles)
    if has_role or not config.monitor_roles:
        return True

    raise commands.CheckFailure("You do not have permissions to use Bailey Bot!")

@bot.command(name="help")
async def help(ctx):
    embed = discord.Embed(title="Bailey Bot Help Menu",
                          description="Guide to configuring Bailey Bot",
                          color=discord.Color.blue()
                         )
    quick_start = """1. Set Log Channel: `$set log <channel>`
2. Add Channels to Monitor: `$add monitor <channel>`
3. Add Monitoring Roles: `$add monitor_role <role>`
4. Toggle Active: `$set active True` (default is True)""" 

    embed.add_field(name="Quick Start", value=quick_start, inline=False)
    embed.add_field(name="$set", value="Adjust bot settings (active, auto, manual, new_only).", inline=False)
    embed.add_field(name="$add/remove", value="Manage monitored channels and monitoring roles.", inline=False)
    embed.add_field(name="$summary", value="View current server configuration.", inline=False)

    await ctx.send(embed=embed)
    

@bot.command(name="summary")
async def summary(ctx):
    """
    Generates a summary of the bot's current configuration.
    """
    
    config = bot.get_config(ctx.guild.id)

    embed = discord.Embed(title="Bailey Bot Configuration", color=discord.Color.blue())

    log_ch = bot.get_channel(config.log_channel_id)
    log_val = log_ch.mention if log_ch else "Not Set (Use `$set log <channel`)"
    embed.add_field(name="Log Channel", value=log_val, inline=False)

    monitor_channel_names = []
    for cid in config.monitor_channels:
        ch = bot.get_channel(cid)
        monitor_channel_names.append(ch.mention if ch else f"Unknown ({cid})")

    monitored_val = ", ".join(monitor_channel_names) if monitor_channel_names else "All Channels (Default)"
    embed.add_field(name="Monitoring Channels", value=monitored_val, inline=False)

    monitored_roles = []
    for rid in config.monitor_roles:
        role = ctx.guild.get_role(rid)
        monitored_roles.append(role)

    monitored_roles_val = ", ".join([r.mention for r in monitored_roles]) if monitored_roles else "None"
    embed.add_field(name="Monitoring Roles", value=monitored_roles_val)

    embed.add_field(name="Auto Ban Threshold", value=config.confidence_auto, inline=False)
    embed.add_field(name="Manual Ban Threshold", value=config.confidence_manual, inline=False)
    embed.add_field(name="Active?", value="Yes" if config.is_active else "No", inline=False)
    embed.add_field(name="Testing?", value="Yes" if config.is_testing else "No", inline=False)
    embed.add_field(name="Check New Only?", value="Yes" if config.new_only else "No", inline=False)

    await ctx.send(embed=embed)


@bot.group(invoke_without_command=True)
async def set(ctx):
    """
    Changes the configuration of the bot's settings.
    """
    pass

@set.command(name="active")
async def set_active(ctx, value: bool):
    """
    Sets whether or not the bot is active.
    """
    config = bot.get_config(ctx.guild.id)
    config.is_active = value
    
    status = "enabled" if value else "disabled"
    await ctx.send(f"Monitoring is now {status}")
    bot.save_configs()

@set.command(name="test")
async def set_test(ctx, value: bool):
    """
    Sets whether or not the bot is in test mode.
    """
    config = bot.get_config(ctx.guild.id)
    config.is_testing = value
    
    status = "enabled" if value else "disabled"
    await ctx.send(f"Testing is now {status}")
    bot.save_configs()

@set.command(name="new_only")
async def set_new_only(ctx, value: bool):
    """
    Sets whether or not the bot will only check messages sent by new members.
    """
    config = bot.get_config(ctx.guild.id)
    config.new_only = value
    
    status = "enabled" if value else "disabled"
    await ctx.send(f"New only is now {status}")
    bot.save_configs()

@set.command(name="auto")
async def set_auto(ctx, value: float):
    """
    Sets the minimum score required for the bot to automatically ban (outside of test mode).
    This score must be between 0.6 and 1.0 and greater than or equal to the manual score.
    """
    config = bot.get_config(ctx.guild.id)

    if value > 1.0 or value < 0.6:
        await ctx.send(f"Automatic confidence must be between 0.6 and 1.0")
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
    """
    Sets the minimum score required for the bot to request a manual ban (outside of test mode).
    This score must be between 0.6 and 1.0 and less than or equal to the automatic score.
    """
    config = bot.get_config(ctx.guild.id)

    if value > 1.0 or value < 0.6:
        await ctx.send(f"Manual confidence must be between 0.6 and 1.0")
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
    """
    FUNCTIONALITY CURRENTLY NOT IMPLEMENTED. Sets the number of messages to check from a new user before ignoring them.
    """
    config = bot.get_config(ctx.guild.id)

    config.message_threshold = value
    await ctx.send(f"Message threshold is now {value}")
    bot.save_configs()

@set.command(name="log")
async def set_log(ctx, channel: discord.TextChannel):
    """
    Sets the channel that all logs are sent to. It is recommended that this is set to a private, permissioned channel.
    """
    config = bot.get_config(ctx.guild.id)

    if channel.id == config.log_channel_id:
        await ctx.send(f"Channel {channel.name} is already the log channel!")
        return

    config.log_channel_id = channel.id
    await ctx.send(f"Channel {channel.name} is now the log channel")
    bot.save_configs()

@bot.group(invoke_without_command=True)
async def add(ctx):
    """
    Adds information such as channels to be monitored and roles that will monitor the bot activity.
    """
    pass

@add.command(name="monitor")
async def add_monitor(ctx, channel: discord.TextChannel):
    """
    Adds a new channel to be monitored by the bot. If no monitors are set, then all channels are monitored by default.
    """
    config = bot.get_config(ctx.guild.id)

    if channel.id in config.monitor_channels:
        await ctx.send(f"Channel {channel.name} is already in monitoring list!")
        return

    config.monitor_channels.append(channel.id)
    await ctx.send(f"Channel {channel.name} has been added to monitoring list")
    bot.save_configs()

@add.command(name="monitor_role")
async def add_monitor_role(ctx, role: discord.Role):
    """
    Adds a new role to act as a monitor to the bot's activity (meaning they will be pinged every time a scam is detected).
    """
    config = bot.get_config(ctx.guild.id)

    if role.id in config.monitor_roles:
        await ctx.send(f"Role {role.mention} is already in monitoring roles list!")
        return

    config.monitor_roles.append(role.id)
    await ctx.send(f"Role {role.mention} has been added to monitoring roles list")
    bot.save_configs()

@bot.group(invoke_without_command=True)
async def remove(ctx):
    """
    Removes information such as channels to be monitored and roles that will monitor the bot activity.
    """
    pass

@remove.command(name="monitor")
async def remove_monitor(ctx, channel: discord.TextChannel):
    """
    Removes a channel to be monitored by the bot. If no monitors are set, then all channels are monitored by default.
    """
    config = bot.get_config(ctx.guild.id)

    if channel.id not in config.monitor_channels:
        await ctx.send(f"Channel {channel.name} not in monitoring list!")
        return

    config.monitor_channels.remove(channel.id)
    await ctx.send(f"Channel {channel.name} removed from monitoring list")
    bot.save_configs()

@remove.command(name="monitor_role")
async def remove_monitor_role(ctx, role: discord.Role):
    """
    Removes a role from acting as a monitor to the bot's activity (meaning they will be pinged every time a scam is detected).
    """
    config = bot.get_config(ctx.guild.id)

    if role.id not in config.monitor_roles:
        await ctx.send(f"Role {role.mention} not in monitoring roles list!")
        return

    config.monitor_roles.remove(role.id)
    await ctx.send(f"Role {role.mention} removed from monitoring roles list!")
    bot.save_configs()



bot.run(token)
