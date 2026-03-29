import configparser

config = {}

def __init__():
    config = configparser.ConfigParser()
    config.read("config.ini")

def get_config():
    return config