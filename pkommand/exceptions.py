"""This modules contains the set of pkommand's exceptions."""


class ParserException(Exception):
    """An exception occurred in :class: `Parser`."""


class NoSubcommandsException(ParserException):
    """An exception when :class: `Parser` without subcommands run."""


class NoDefaultRunException(ParserException):
    """An exception when :class: `Parser` without default run implementation."""
