"""This modules contains subcommand templates."""

from abc import ABC, abstractmethod
from argparse import ArgumentParser, Namespace, _SubParsersAction
from typing import Dict, List, Optional, cast, final


class Command(ABC):
    """A subcommand template."""

    @classmethod
    @final
    def new(cls) -> "Command":
        """Return a new `Command`."""
        return cls()

    @staticmethod
    @abstractmethod
    def name() -> str:
        """Return command name."""

    @classmethod
    @abstractmethod
    def help(cls) -> str:
        """Return command help."""

    @abstractmethod
    def run(self, args: Namespace):
        """Execute the command.

        :param args: command arguments
        """

    @classmethod
    @abstractmethod
    def register(cls, parser: ArgumentParser):
        """Register arguments to parser.

        :param parser: command parser for this command
        """

    @classmethod
    def register_parser(cls, subparsers: _SubParsersAction) -> ArgumentParser:
        """Register the command to subparser."""
        p = subparsers.add_parser(cls.name(), help=cls.help())
        cls.register(p)
        return p


class CommandClassDict:
    """A dictionary contains :class: `Command` only."""

    __class_dict: Dict[str, type]

    def __init__(self):  # noqa
        self.__class_dict = {}

    def get(self, key: str) -> Optional[type]:
        """Return a :class: `Command` type.

        Returns None if not found.
        :param key: `Command.name` 's value you search
        """
        return self.__class_dict.get(key)

    def get_instance(self, key: str) -> Optional[Command]:
        """Return a `Command`.

        Returns None if not found.
        :param key: `Command.name` 's value you search
        """
        c = self.get(key)
        if not c:
            return None
        return cast(Command, c.new())  # type: ignore

    def set(self, value):
        """Store a :class: `Command` type.

        :param value: type whose bases contain :class: `Command`
        """
        if Command not in value.__bases__:
            raise TypeError(
                "unsupported value type: {}'s bases doesn't have Command".format(value)
            )
        key = value.name()
        self.__class_dict[key] = value

    def keys(self) -> List[str]:
        """Return all keys."""
        return list(self.__class_dict.keys())
