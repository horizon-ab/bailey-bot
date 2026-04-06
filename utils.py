

class ServerConfig:
    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.monitor_channels = []
        self.confidence_auto = 0.9
        self.confidence_manual = 0.7
        self.message_threshold = 3
        self.is_active = True
        self.is_testing = True
        self.log_channel_id = None

    def to_dict(self):
        return {
            "monitor_channels" : self.monitor_channels,
            "confidence_auto" : self.confidence_auto,
            "confidence_manual" : self.confidence_manual,
            "message_threshold" : self.message_threshold,
            "is_active" : self.is_active,
            "is_testing" : self.is_testing,
            "log_channel_id" : self.log_channel_id
        }

    @classmethod
    def from_dict(cls, guild_id, data):
        config = cls(guild_id)
        config.monitor_channels = data.get("monitor_channels", [])
        config.confidence_auto = data.get("confidence_auto", 0.9)
        config.confidence_manual = data.get("confidence_manual", 0.7)
        config.message_threshold = data.get("message_threshold", 3)
        config.is_active = data.get("is_active", True)
        config.is_testing = data.get("is_testing", True)
        config.log_channel_id = data.get("log_channel_id")
        return config

