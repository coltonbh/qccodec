class BaseError(Exception):
    """Base qccodec exceptions"""


class DecoderError(BaseError):
    """Exception raised when a decoder error occurs"""


class EncoderError(BaseError):
    """Exception raised when a encoder error occurs"""


class ParserError(BaseError):
    """Base exception for parsers"""

    def __init__(self, message: str, data=None):
        super().__init__(message)
        self.data = data


class MatchNotFoundError(ParserError):
    """Exception raised when a parsing match is not found"""

    def __init__(self, regex: str, contents: str):
        self.regex = regex
        self.contents = contents
        super().__init__(
            f"Could not locate match for regex: '{regex}' in contents: '{contents}'"
        )


class RegistryError(BaseError):
    """Exception raised when a registry error occurs"""


class DataCollectorError(BaseError):
    """Exception raised when a data collector error occurs"""
