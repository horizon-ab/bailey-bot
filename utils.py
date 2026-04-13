# utils.py

import discord

class ServerConfig:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.monitor_channels = []
        self.monitor_roles = []
        self.confidence_auto = 0.9
        self.confidence_manual = 0.7
        self.message_threshold = 3
        self.is_active = True
        self.is_testing = True
        self.new_only = True
        self.log_channel_id = None

    def to_dict(self):
        return {
            "monitor_channels" : self.monitor_channels,
            "monitor_roles" : self.monitor_roles,
            "confidence_auto" : self.confidence_auto,
            "confidence_manual" : self.confidence_manual,
            "message_threshold" : self.message_threshold,
            "is_active" : self.is_active,
            "is_testing" : self.is_testing,
            "new_only" : self.new_only,
            "log_channel_id" : self.log_channel_id
        }

    @classmethod
    def from_dict(cls, guild_id, data):
        config = cls(guild_id)
        config.monitor_channels = data.get("monitor_channels", [])
        config.monitor_roles = data.get("monitor_roles", [])
        config.confidence_auto = data.get("confidence_auto", 0.9)
        config.confidence_manual = data.get("confidence_manual", 0.7)
        config.message_threshold = data.get("message_threshold", 3)
        config.is_active = data.get("is_active", True)
        config.is_testing = data.get("is_testing", True)
        config.new_only = data.get("new_only", True)
        config.log_channel_id = data.get("log_channel_id")
        return config

class ScamReviewView(discord.ui.View):
    def __init__(self, bot, msg, score):
        super().__init__(timeout=3600)
        self.bot = bot
        self.msg = msg
        self.score = score

    @discord.ui.button(label="Ban User", style=discord.ButtonStyle.danger)
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message("You don't have permission to ban!", ephemeral=True)

        try:
            await self.msg.author.ban(reason=f"Manual Scam Review: {self.score:.2f}")
            await interaction.response.edit_message(content=f"User {self.msg.author.name} banned by {interaction.user.name}", view=None)

        except discord.Forbidden:
            await interaction.response.send_message("Error: My role is too low to ban this user.", ephemeral=True)

    @discord.ui.button(label="Ignore", style=discord.ButtonStyle.secondary)
    async def ignore_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(content=f"Ignored by {interaction.user.name}", view=None)
