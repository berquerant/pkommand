"""This module contains :class: `argparse.ArgumentParser` extensions for subcommand."""

import sys
from argparse import ArgumentParser
from typing import List, Optional

from .command import Command, CommandClassDict
from .exceptions import NoDefaultRunException, NoSubcommandsException, ParserException


class Parser(ArgumentParser):
    """An ArgumentParser using :class: `Command`."""

    __ccd: CommandClassDict

    def __init__(self, *args, **kwargs):  # noqa
        super().__init__(*args, **kwargs)
        self.__ccd = CommandClassDict()

    def error(self, message: str):  # noqa
        # avoid exiting directly on parse_args error
        raise ParserException(message)

    def _get_command_instance(self, command_name: str) -> Optional[Command]:
        return self.__ccd.get_instance(command_name)

    def _get_command_names(self) -> List[str]:
        return self.__ccd.keys()

    def add_command_class(self, command_class):
        """Append a subcommand.

        :param command_class: type whose bases contain :class: `Command`
        """
        self.__ccd.set(command_class)

    def _register_commands(self):
        if not self._get_command_names():
            raise NoSubcommandsException()
        sp = self.add_subparsers(dest="command")
        for command_name in self._get_command_names():
            self._get_command_instance(command_name).register_parser(sp)

    def run(self, args=None, namespace=None):
        """Parse arguments and try to execute subcommand.

        :param args: (optional) string list to be parsed
        :param namespace: (optional) object to be assigned attributes
        """
        args = self.parse_args(args=args, namespace=namespace)
        if not args:
            return
        if not args.command:
            self.default_run(args=args, namespace=namespace)
            return
        self._get_command_instance(args.command).run(args)

    def default_run(self, args=None, namespace=None):
        """Execute a process when no subcommand specified.

        You can override this if you also want to run without subcommand name.

        :param args: (optional) string list to be parsed
        :param namespace: (optional) object to be assigned attributes
        """
        raise NoDefaultRunException()

    def parse_args(self, args=None, namespace=None):  # noqa
        self._register_commands()
        try:
            return super().parse_args(args=args, namespace=namespace)
        except Exception as e:  # pylint: disable=broad-except
            self.on_parse_exception(exc=e, file=sys.stderr)
            return None

    def on_parse_exception(self, exc: Exception, file=None):
        """Execute on parse exception.

        :param exc: raised exception on parse
        :param file: output stream
        """
        print(exc, file=file)
        self.print_help(file=file)
        sys.exit(1)
