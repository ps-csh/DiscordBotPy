import configparser
from functools import wraps
import logging
from bot.command_registry import CommandData, CommandResult, register_command

_logger = logging.getLogger(__name__)
_config = configparser.ConfigParser()
_config.read("config.ini")
_admin_id = _config["bot"]["admin_id"]

def command(name):
    def wrapper(func):
        #Calls register_command in command_registry to ensure it is added to the list of commands
        register_command(name, func)        
        return func
    return wrapper

def admin(func: function):
    """Restricts the command to only be executed by the admin, specified in the config"""
    @wraps(func)    #preserves metadata
    def wrapper(cmd: CommandData, *args, **kwargs): #args and kwargs ensure this doesn't break if parameters are added later
        try:
            _logger.debug(f"Authorizing user: {cmd.payload.author} against {_admin_id}")
            if cmd.payload.author["id"] == _admin_id:
                return func(cmd, *args, **kwargs)
            return CommandResult(status = CommandResult.UNAUTHORIZED, 
                                message = "This command requires admin privileges")
        except Exception as e:
            _logger.error(f"Failed to execute admin decorator in {func.__name__}\n{e}")
        return CommandResult(status= CommandResult.ERROR, message="Something went wrong.")
    return wrapper

def authorize(users: list):
    """Restricts the command to only be executed by authorized users, specified in the config"""
    def decorator(func: function):
        @wraps(func)    #preserves metadata
        def wrapper(cmd: CommandData, *args, **kwargs): #args and kwargs ensure this doesn't break if parameters are added later
            try:
                #TODO: Get list of users from external file or database
                _logger.debug(f"Authorizing user: {cmd.payload.author} against {_admin_id}")
                if cmd.payload.author["id"] == _admin_id:
                    return func(cmd, *args, **kwargs)
                return CommandResult(status = CommandResult.UNAUTHORIZED, 
                                    message = "This command requires admin privileges")
            except Exception as e:
                _logger.error(f"Failed to execute admin decorator in {func.__name__}\n{e}")
            return None
        return wrapper
    return decorator

def args(count: int):
    """
    Specifies the expected amount of arguments for a given command.
    Splits the string to match the number of arguments.
    """
    assert count > 0
    def decorator(func: function):
        @wraps(func)    #preserves metadata
        def wrapper(cmd: CommandData, *args, **kwargs): #args and kwargs ensure this doesn't break if parameters are added later
            try:
                command_args = cmd.command_string.split(maxsplit=count)
                if len(command_args) > count:
                    cmd.command_args = command_args[1:]
                    return func(cmd, *args, **kwargs)
                return CommandResult(status = CommandResult.FAIL, 
                                    message = f"Incorrect number of arguments. Expected {count}\nargs received: {cmd.command_args}")
            except Exception as e:
                _logger.error(f"Failed to execute admin decorator in {func.__name__}\n{e}")
            return None
        return wrapper
    return decorator