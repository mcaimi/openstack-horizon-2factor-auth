# 2FA custom exceptions

class IllegalArgument(Exception):
    pass

class InvalidToken(Exception):
    pass

class TOTPRuntimeError(Exception):
    pass
