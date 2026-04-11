# Conversion classes for Discord Gateway payloads as Json data
# Received as the 'd' field in the gateway event
import json
import random
from dataclasses import dataclass

from discordapi.structures.discord_enums import DiscordGatewayOpcode

class DiscordStructure:
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__)

# Data structure received during Discord gateway events
class DiscordGatewayEvent(DiscordStructure):
    op: DiscordGatewayOpcode | int #OpCode indicating the type of message
    d: str | any #Payload, assumes to be a JSON object
    s: int #Sequence number, only present in OpCode 0
    t: str  #Event type, only used for OpCode 0

    def __init__(self, 
                 op: DiscordGatewayOpcode|int, 
                 d: str|any = None, 
                 s:int = None,
                 t: str = None):
        self.op = op
        self.d = d
        self.s = s
        self.t = t

    # def to_json(self):
    #     return json.dumps(self, default=lambda o: o.__dict__)

class DiscordHelloPayload:
    heartbeat_interval: int

    def __init__(self, interval):
        self.heartbeat_interval = interval

class DiscordIdentifyPayload:
    # Authentication token
    token: str

    properties: any = {}

    large_threshold: int

    #false by default
    compress: bool

#TODO: Implement these payloads
#Shard - array of two integers, unused since this isn't a public bot
#Presence
#

    # Gateway Intents you wish to receive 
    intents: int

    def __init__(self, token: str, 
                 device: str, 
                 intents: int,
                 os: str = None, 
                 browser: str = None, 
                 large_threshold: int = 50, 
                 compress: bool = False):
       self.token = token
       self.properties = {"os": os, "browser": browser, "device": device}
       #self.properties.os = os
       #self.properties.browser = browser
       #self.properties.device = device
       self.large_threshold = large_threshold
       self.compress = compress
       self.intents = intents

    def to_json(self):
        return {"token": self.token, 
                "properties": {"device": self.properties["device"], "browser": self.properties["browser"], "os": self.properties["os"]}, 
                "large_threshold": self.large_threshold, 
                "compress": self.compress, 
                "intents": self.intents}


#Note - dataclass requires nullable fields to be declared after required fields
# for __init__ to be generated correctly
@dataclass
class DiscordMessagePayload:
    """ 
    Payload received during MESSAGE_CREATE, MESSAGE_UPDATE, MESSAGE_DELETE events\n
    see: https://docs.discord.com/developers/resources/message
    """

# Message ID
# Type: snowflake
    id: str 

    channel_id: str

# The author of this message.
# Not guaranteed to be a valid user, such as messages
# created through webhooks.
#DiscordUserObjectStructure 
    author: any

    # ISO8601 timestamp of when the message was created
    timestamp: str

    # ISO8601 timestamp of when message was last edited
    edited_timestamp: str | None

    content: str

    # Text-to-speech
    tts: bool

#[JsonProperty("mention_everyone")]
    mention_everyone: bool

#DiscordUserObjectStructure
    mentions: list

    # Array of mentioned Role IDs
    mention_roles: list

    attachments: list

    embeds: list

    pinned: bool

    type: int
    """
    The type of message. For list of types see: 
    https://discord.com/developers/docs/resources/channel#message-object-message-types"
    """

# region Nullable fields, not guaranteed to exist in the payload
    mention_channels: list | None = None

    reactions: list | None = None

    # For validating when a message was sent. Can be an integer or string
    nonce: str | int | None = None

    webhook_id: str | None = None

    activity: any | None = None
    application: any | None = None
    application_id: any | None = None
    flags: int | None = None
    message_reference: any | None = None
    message_snapshots: any | None = None
    referenced_message: any | None = None
    interaction_metadata: any | None = None
    interaction: any | None = None
    thread: any | None = None
    components: any | None = None
    sticker_items: any | None = None
    stickers: list | None = None
    position: any | None = None
    role_subscription_data: any | None = None
    resolved: any | None = None
    poll: any | None = None
    call: any | None = None
    shared_client_theme: any | None = None

    #NOTE - this field is not listed in the Discord Docs, but is present in MESSAGE_CREATE events
    # may be a replacement for channel.type, as partial channels aren't sent here
    channel_type: any | None = None

    #The following fields are unique to the MESSAGE_CREATE and MESSAGE_UPDATE dispatch event type
    # sent from text-based guilds.
    #see: https://docs.discord.com/developers/events/gateway-events#message-create
    guild_id: str | None = None
    # DiscordGuildMemberStructure? 
    member: any = None
# endregion
#
#TODO:
#Activity
#
#Application
#
#MessageReference
#
#Flags
#
#Stickers
#
#ReferencedMessage

# #TODO: ensure all non-nullable fields are handled so Json can be converted
#     def __init__(self, 
#                  id, 
#                  channel_id, 
#                  author,
#                  content, 
#                  timestamp,
#                  edited_timestamp,
#                  tts,
#                  mention_everyone,
#                  mentions,
#                  mention_roles,
#                  attachments,
#                  embeds,
#                  nonce,
#                  pinned: bool,
#                  type):
#         self.id = id
#         self.channel_id = channel_id
#         self.author = author
#         self.content = content
#         self.timestamp = timestamp
#         self.edited_timestamp = edited_timestamp
#         self.tts = tts
#         self.type = type
#         pass




class DiscordSendMessageStructure(DiscordStructure):
    # Nonce values are random numbers, up to 25 characters?
    NONCE_MIN: int = 100000000;
    NONCE_MAX: int = 1000000000;

    content: str | None

# Nonce can accept an integer or string value
    nonce: str | None

# Text-to-speech
    tts: bool = False

#TODO:
# Up to 10 embeds, max 6000 characters total
#public List<DiscordEmbedObjectStructure> Embeds { get; set; } = [];
    embeds: list | None

#public AllowedMentions? {get; set;}

#TODO: structure as AllowedMentions class
#[JsonProperty("allowed_mentions")]
    #allowed_mentions: str | None

#message_reference

#components

# Ids of up to 3 stickers in the server to send
    sticker_ids: list | None

#Note - property name must be "files[n]", where "n" is the number of files
#will probably require custom serializer
    #files: str | None

# Json encoded additional request fields, only for multipart messages
#[JsonProperty("payload_json")]
    payload_json: str | None

#Array of partial attachments
#attachments

#TODO: Implement Message Flags bitfield: https://discord.com/developers/docs/resources/channel#message-object-message-flags
    flags: int | None = None

#If true and nonce is present, it will be checked for uniqueness in the past few minutes.
#If another message was created by the same author with the same nonce, that message will be returned and no new message will be created.
    enforce_nonce: bool

    def __init__(self, content, tts = False):
        super().__init__()
        self.nonce = random.randint(self.NONCE_MIN, self.NONCE_MAX)
        self.content = content
        self.tts = tts