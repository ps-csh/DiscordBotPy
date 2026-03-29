# Conversion classes for Discord Gateway payloads as Json data
# Received as the 'd' field in the gateway event

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