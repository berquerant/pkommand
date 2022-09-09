"""This module contains :class: `argparse.ArgumentParser` extensions for subcommand."""

import sys
from argparse import ArgumentParser, Namespace
from typing import Callable, Dict, List, Optional

from .command import Command, CommandClassDict
from .exceptions import NoDefaultRunException, NoSubcommandsException, ParserException


class HelpCommand(Command):
    """Default help command."""

    @staticmethod
    def name() -> str:  # noqa
        return "help"

    @classmethod
    def help(cls) -> str:  # noqa
        return "show help and exit"

    def run(self, _):  # noqa
        pass

    @classmethod
    def register(cls, parser: ArgumentParser):  # noqa
        parser.add_argument("subcommand", nargs="?")


def default_run_print_help(
    parser: ArgumentParser,
    args: Optional[List[str]] = None,
    namespace: Optional[Namespace] = None,
):
    """Print help of `parser`."""
    parser.print_help()


class Parser(ArgumentParser):
    """An ArgumentParser using :class: `Command`."""

    __ccd: CommandClassDict
    __subparsers: Dict[str, ArgumentParser]
    __default_run: Optional[
        Callable[[ArgumentParser, Optional[List[str]], Optional[Namespace]], None]
    ]

    def __init__(
        self,
        add_help=False,
        default_run: Optional[
            Callable[[ArgumentParser, Optional[List[str]], Optional[Namespace]], None]
        ] = default_run_print_help,
        *args,
        **kwargs,
    ):  # noqa
        """Return a new `Parser`.

        :add_help: add `-h/--help` option.
        :default_run: set default_run function. This has the same effect as overriding `default_run`."""
        kwargs["add_help"] = add_help
        super().__init__(*args, **kwargs)
        self.__default_run = default_run
        self.__ccd = CommandClassDict()
        self.add_command_class(HelpCommand)
        self.__subparsers = {}

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

    def _get_subparser(self, command_name: str) -> Optional[ArgumentParser]:
        return self.__subparsers.get(command_name)

    def _add_subparser(self, command_name: str, p: ArgumentParser):
        self.__subparsers[command_name] = p

    def _register_commands(self):
        if not self._get_command_names():
            raise NoSubcommandsException()
        sp = self.add_subparsers(dest="command")
        for command_name in self._get_command_names():
            self._add_subparser(
                command_name,
                self._get_command_instance(command_name).register_parser(sp),
            )

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
        if args.command == "help":
            if not args.subcommand:
                self.print_help()
                return
            subparser = self._get_subparser(args.subcommand)
            instance = self._get_command_instance(args.subcommand)
            if not (subparser and instance):
                print(f"unknown command: {args.subcommand}", file=sys.stderr)
                self.print_help()
                return
            subparser.print_help()
            print()
            print(instance.help())
            return
        self._get_command_instance(args.command).run(args)

    def default_run(
        self, args: Optional[List[str]] = None, namespace: Optional[Namespace] = None
    ):
        """Execute a process when no subcommand specified.

        You can override this if you also want to run without subcommand name.

        :param args: (optional) string list to be parsed
        :param namespace: (optional) object to be assigned attributes
        """
        if self.__default_run:
            self.__default_run(self, args, namespace)
            return
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
