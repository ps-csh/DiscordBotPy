# Conversion classes for Discord Gateway events as Json data

import enum
import json

# Discord Gateway Opcodes representing the type of message
# "https://discord.com/developers/docs/topics/opcodes-and-status-codes#gateway"
class DiscordGatewayOpcode(enum.IntEnum):
                                #Event is sent by client or received by client (from API)
    Dispatch = 0                #Recieve
    Heartbeat = 1               #Send
    Identify = 2                #Send
    PresenceUpdate = 3          #Send
    VoiceStateUpdate = 4        #Send, Receive
    #OpCode 5 is not used by Discord API
    Resume = 6                  #Send
    Reconnect = 7               #Receive
    RequestGuildMembers = 8     #Send
    InvalidSession = 9          #Receive
    Hello = 10                  #Receive
    HeartbeatAcknowledge = 11   #Receive

# Flags representing Gateway Intents for the app to receive from the Discord Gateway
class DiscordGatewayIntents(enum.IntFlag):
    NoIntents = 0
    Guilds = 1 << 0
    GuildMembers = 1 << 1
    GuildModeration = 1 << 2
    GuildEmojisAndStickers = 1 << 3
    GuildIntegrations = 1 << 4
    GuildWebhooks = 1 << 5
    GuildInvites = 1 << 6
    GuildVoiceStates = 1 << 7
    GuildPresences = 1 << 8
    GuildMessages = 1 << 9
    GuildMessageReactions = 1 << 10
    GuildMessageTyping = 1 << 11
    DirectMessages = 1 << 12
    DirectMessageReactions = 1 << 13
    DirectMessageTyping = 1 << 14
    MessageContent = 1 << 15
    GuildScheduledEvents = 1 << 16
    AutoModerationConfiguration = 1 << 20
    AutoModerationExecutions = 1 << 21

class DiscordGatewayEventType:
    MESSAGE_CREATE = "MESSAGE_CREATE"
    MESSAGE_UPDATE = "MESSAGE_UPDATE"
    CHANNEL_CREATE = "CHANNEL_CREATE"
    CHANNEL_UPDATE = "CHANNEL_UPDATE"
    CHANNEL_DELETE = "CHANNEL_DELETE"
    THREAD_CREATE = "THREAD_CREATE"
    THREAD_UPDATE = "THREAD_UPDATE"
    THREAD_DELETE = "THREAD_DELETE"
    GUILD_CREATE = "GUILD_CREATE"
    GUILD_UPDATE = "GUILD_UPDATE"
    GUILD_DELETE = "GUILD_DELETE"
    GUILD_EMOJIS_UPDATE = "GUILD_EMOJIS_UPDATE"
    GUILD_STICKERS_UPDATE = "GUILD_STICKERS_UPDATE"
    GUILD_MEMBER_ADD = "GUILD_MEMBER_ADD"
    GUILD_MEMBER_REMOVE = "GUILD_MEMBER_REMOVE"
    GUILD_MEMBER_UPDATE = "GUILD_MEMBER_UPDATE"
    MESSAGE_REACTION_ADD = "MESSAGE_REACTION_ADD"
    MESSAGE_REACTION_REMOVE = "MESSAGE_REACTION_REMOVE"
    PRESENCE_UPDATE = "PRESENCE_UPDATE"
    VOICE_STATE_UPDATE = "VOICE_STATE_UPDATE"
    VOICE_SERVER_UPDATE = "VOICE_SERVER_UPDATE"


