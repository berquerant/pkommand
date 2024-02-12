""":class: `argparse.ArgumentParser` extensions for subcommand."""

import sys
from argparse import ArgumentParser, Namespace
from typing import Callable, NoReturn, override

from .command import Command, CommandClassDict
from .exceptions import NoDefaultRunException, NoSubcommandsException, ParserException


class HelpCommand(Command):
    """Default help command."""

    @override
    @staticmethod
    def name() -> str:  # noqa
        return "help"

    @override
    @classmethod
    def help(cls) -> str:  # noqa
        return "show help and exit"

    @override
    def run(self, _) -> None:  # noqa
        pass

    @override
    @classmethod
    def register(cls, parser: ArgumentParser) -> None:  # noqa
        parser.add_argument("subcommand", nargs="?")


def default_run_print_help(
    parser: ArgumentParser,
    args: list[str] | None = None,
    namespace: Namespace | None = None,
):
    """Print help of `parser`."""
    parser.print_help()


class Parser(ArgumentParser):
    """An ArgumentParser using :class: `Command`."""

    __ccd: CommandClassDict
    __subparsers: dict[str, ArgumentParser]
    __default_run: Callable[[ArgumentParser, list[str] | None, Namespace | None], None] | None

    def __init__(
        self,
        add_help=False,
        default_run: (
            Callable[[ArgumentParser, list[str] | None, Namespace | None], None] | None
        ) = default_run_print_help,
        *args,
        **kwargs,
    ):  # noqa
        """
        Return a new `Parser`.

        :add_help: add `-h/--help` option.
        :default_run: set default_run function. This has the same effect as overriding `default_run`.
        """
        kwargs["add_help"] = add_help
        super().__init__(*args, **kwargs)
        self.__default_run = default_run
        self.__ccd = CommandClassDict()
        self.add_command_class(HelpCommand)
        self.__subparsers = {}

    def error(self, message: str) -> NoReturn:  # noqa
        # avoid exiting directly on parse_args error
        raise ParserException(message)

    def _get_command_instance(self, command_name: str) -> Command | None:
        return self.__ccd.get_instance(command_name)

    def _get_command_names(self) -> list[str]:
        return self.__ccd.keys()

    def add_command_class(self, command_class) -> None:
        """
        Append a subcommand.

        :param command_class: type whose bases contain :class: `Command`
        """
        self.__ccd.set(command_class)

    def _get_subparser(self, command_name: str) -> ArgumentParser | None:
        return self.__subparsers.get(command_name)

    def _add_subparser(self, command_name: str, p: ArgumentParser) -> None:
        self.__subparsers[command_name] = p

    def _register_commands(self) -> None:
        if not self._get_command_names():
            raise NoSubcommandsException()
        sp = self.add_subparsers(dest="command")
        for command_name in self._get_command_names():
            c = self._get_command_instance(command_name)
            if not c:
                raise NoSubcommandsException(command_name)
            self._add_subparser(
                command_name,
                c.register_parser(sp),
            )

    def run(self, args=None, namespace=None) -> None:
        """
        Parse arguments and try to execute subcommand.

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
        c = self._get_command_instance(args.command)
        if not c:
            raise NoSubcommandsException(args.command)
        c.run(args)

    def default_run(self, args: list[str] | None = None, namespace: Namespace | None = None):
        """
        Execute a process when no subcommand specified.

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

    def on_parse_exception(self, exc: Exception, file=None) -> NoReturn:
        """
        Execute on parse exception.

        :param exc: raised exception on parse
        :param file: output stream
        """
        print(exc, file=file)
        self.print_help(file=file)
        sys.exit(1)
