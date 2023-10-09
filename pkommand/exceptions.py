"""Set of pkommand's exceptions."""


class ParserException(Exception):
    """An exception occurred in :class: `Parser`."""


class NoSubcommandsException(ParserException):
    """An exception when :class: `Parser` without subcommands run."""


class NoDefaultRunException(ParserException):
    """An exception when :class: `Parser` without default run implementation."""


class WrapperException(Exception):
    """An exception from wrapper module."""


class ContainerException(Exception):
    """An exception from container."""
