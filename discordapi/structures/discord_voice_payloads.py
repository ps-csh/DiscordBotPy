from dataclasses import dataclass
from discord_payloads import DiscordStructure

@dataclass
class DiscordVoiceStateObject(DiscordStructure):
    """
    Represents a user's voice connection status\n
    See: https://docs.discord.com/developers/resources/voice#voice-state-object
    """

    channel_id: str
    user_id: str
    session_id: str
    deaf: bool
    mute: bool
    self_deaf: bool
    self_mute: bool
    self_video: bool
    suppress: bool
    request_to_speak_timestamp: any | None

    guild_id: str | None = None
    member: any | None = None
    self_stream: bool | None = None

@dataclass
class DiscordVoiceServerUpdate(DiscordStructure):
    """
    Sent when the guild's voice server is updated.
    Includes when connecting to voice, and when instance changes to a new server.
    """
    token: str
    guild_id: str
    endpoint: str | None
    """
    If endpoint is null, it means the server is being reallocated and user should 
    disconnect from current one and wait for reallocation.
    """