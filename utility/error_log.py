
from bot.command_registry import CommandResult

MAX_ERRORS = 10

_errors: list = []

def add_error(error_result: CommandResult):
    if len(_errors) >= MAX_ERRORS:
        del _errors[0]
    _errors.append(error_result)

def get_error(index: int):
    if index >= 0 and index < len(_errors):
        return _errors[index]
    return None

def last_error():
    count = len(_errors)
    return _errors[count - 1] if count > 0 else None