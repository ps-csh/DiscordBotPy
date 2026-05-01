from dataclasses import dataclass
import random
from discordapi.structures.discord_payloads import DiscordStructure

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
    #Not mentioned in docs
    discoverable: bool | None = None
    connected_at: any | None = None
    preferred_region: any | None = None
    preferred_regions: any | None = None

class DiscordVoiceUpdatePayload(DiscordStructure):
    """{
    "op": 4,
    "d": {
        "guild_id": "41771983423143937",
        "channel_id": "127121515262115840",
        "self_mute": false,
        "self_deaf": false
    }
    }"""
    guild_id: int
    channel_id: str
    self_mute: bool
    self_deaf: bool

    def __init__(self, guild_id: str, channel_id: str, self_mute: bool, self_deaf: bool):
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.self_mute = self_mute
        self.self_deaf = self_deaf

@dataclass
class DiscordVoiceServerUpdatePayload(DiscordStructure):
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

class DiscordVoiceIdentifyPayload(DiscordStructure):
    """
    "server_id": "41771983423143937",
    "user_id": "104694319306248192",
    "session_id": "my_session_id",
    "token": "my_token",
    "max_dave_protocol_version": 1
    """
    server_id: str
    user_id: str
    session_id: str
    token: str
    max_dave_protocol_version: int

    def __init__(self, server_id, user_id, session_id, token, max_dave_protocol_version = 1):
        self.server_id = server_id
        self.user_id = user_id
        self.session_id = session_id
        self.token = token
        self.max_dave_protocol_version = max_dave_protocol_version

# Contains SSRC, UDP IP/port, and supported encryption modes the voice server expects
# https://docs.discord.com/developers/topics/voice-connections#establishing-a-voice-websocket-connection
@dataclass
class DiscordVoiceReadyPayload(DiscordStructure):
    """{
    "op": 2,
    "d": {
        "ssrc": 1,
        "ip": "127.0.0.1",
        "port": 1234,
        "modes": ["xsalsa20_poly1305", "xsalsa20_poly1305_suffix", "xsalsa20_poly1305_lite"],
        "heartbeat_interval": 1
    }
    }"""
    ssrc: int
    ip: str
    port: int
    modes: list

    experiments: any | None
    streams: any | None
    heartbeat_interval: int | None = None
    """This is an erroneous field. Heartbeat interval should be parsed from Hello payload instead"""


_NONCE_MIN: int = 100000000;
_NONCE_MAX: int = 1000000000;
class DiscordVoiceHeartbeatPayload(DiscordStructure):

    t: int
    seq_ack: int | None
    """seq_ack is the last sequence number received from the gateway, and is required since gateway v8"""

    def __init__(self, seq_ack: int, t: int| None = None):
        self.t = t if t else random.randint(_NONCE_MIN, _NONCE_MAX)
        self.seq_ack = seq_ack

class DiscordVoiceSelectProtocolPayload(DiscordStructure):
    protocol: str
    data: dict

    def __init__(self, address, port, mode):
        super().__init__()
        self.protocol = 'udp'
        self.data = {"address": address, "port": port, "mode": mode}

#NOTE - Discord docs contains outdated information
#See - https://docs.discord.food/topics/voice-connections#session-description-structure
@dataclass
class DiscordVoiceSessionDescriptionPayload(DiscordStructure):
    audio_codec: str
    video_codec: str
    media_session_id: str
    dave_protocol_version: int
    mode: str | None = None
    secret_key: list | None = None
    sdp: str | None = None
    keyframe_interval: int | None = None

    #Seems to be an int, not mentioned in docs
    secure_frames_version: int | None = None