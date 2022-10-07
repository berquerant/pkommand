"""This module provides a function-based CLI."""
from abc import ABC, abstractmethod
from argparse import Action, ArgumentParser, Namespace
from dataclasses import dataclass
from functools import cached_property
from inspect import Parameter, Signature, isfunction, signature
from textwrap import dedent
from typing import Any, Callable, Protocol, cast

from .command import Command
from .container import Opt, get_attribute
from .exceptions import WrapperException
from .parser import Parser


class BadTargetException(WrapperException):
    """An exception when wrapper received a bad object."""


@dataclass
class Default:
    """Default value of the function parameter."""

    val: Any

    @staticmethod
    def new(p: Parameter) -> "Opt[Default]":
        """Return a new `Default`."""
        if p.default == Parameter.empty:
            return Opt.none()
        return Opt.some(Default(val=p.default))


@dataclass
class Annotation:
    """Annotation of the function parameter."""

    typ: Any

    @staticmethod
    def new(p: Parameter) -> "Opt[Annotation]":
        """Return a new `Annotation`."""
        if p.annotation == Parameter.empty:
            return Opt.none()
        return Opt.some(Annotation(typ=p.annotation))

    @property
    def name(self) -> str:
        """
        Name of the annotation.

        e.g. List of List[T], Optional of Optional[T]
        """
        return get_attribute(self.typ, "_name").get_or(self.typ.__name__)

    @property
    def type(self) -> Any:
        """
        Type of the annotation.

        e.g. bool of bool, T of List[T], Optional[T]
        """
        return (
            get_attribute(self.typ, "__args__")
            .and_then(lambda x: x[0])
            .get_or(self.typ)
        )

    @property
    def wrapped(self) -> bool:
        """Annotation type is generic or not."""
        return hasattr(self.typ, "__args__")


@dataclass
class Param:
    """Wrapper of `inspect.Parameter`."""

    p: Parameter
    abbr: bool = False

    @staticmethod
    def new(p: Parameter, abbr: bool = False) -> "Param":
        """Return a new `Param`."""
        return Param(p=p, abbr=abbr)

    @property
    def name(self) -> str:
        """Name of the paramater."""
        return self.p.name

    @property
    def annotation(self) -> Opt[Annotation]:
        """Annotation of the parameter."""
        return Annotation.new(self.p)

    @property
    def default(self) -> Opt[Default]:
        """Return default value of the parameter."""
        return Default.new(self.p)

    @property
    def flag_names(self) -> list[str]:
        """Names of the parameter as a CLI flag."""
        name = self.p.name
        normal = f"--{name}"
        if not self.abbr:
            return [normal]
        abbr = f"-{name[0]}"
        if len(self.p.name) == 1:
            return [abbr]
        return [abbr, normal]

    def __str__(self) -> str:
        """Return a string expression."""
        return str(self.p)


@dataclass
class RegArg:
    """Arguments for `argparse.Parser.add_argument`."""

    args: list[Any]
    kwargs: dict[str, Any]

    def apply(self, p: ArgumentParser):
        """Call `add_argument`."""
        p.add_argument(*self.args, **self.kwargs)


class RegArgList(list[RegArg]):
    """List of `RegArg`."""

    def apply(self, p: ArgumentParser):
        """Call `add_argument`."""
        for a in self:
            a.apply(p)


class ParamToArg(ABC):
    """Function parameter to `RegArg` converter."""

    @abstractmethod
    def parse(self, p: Param) -> Opt[RegArg]:
        """Parse function parameter to `RegArg`."""
        return Opt.none()

    def __call__(self, p: Param) -> Opt[RegArg]:
        """Convert a function parameter into `RegArg`."""
        return p.annotation.and_then(lambda _: self.parse(p)).flatten()


class BoolParamToArg(ParamToArg):
    """Bool parameter to `RegArg` converter."""

    def parse(self, p: Param) -> Opt[RegArg]:
        """Parse a function parameter into `RegArg`."""
        a = p.annotation.get()
        if a.type != bool or a.wrapped:
            return Opt.none()

        action = p.default.and_then(
            lambda x: "store_false" if x.val else "store_true"
        ).get_or("store_true")
        return Opt.some(
            RegArg(
                args=p.flag_names,
                kwargs={
                    "action": action,
                },
            ),
        )


class DefaultParamToArg(ParamToArg):
    """Default parameter to `RegArg` converter."""

    def parse(self, p: Param) -> Opt[RegArg]:
        """Parse a function parameter into `RegArg`."""
        a = p.annotation.get()
        if a.wrapped:
            return Opt.none()
        kwargs = {
            "type": a.type,
        }
        if p.default.is_some:
            kwargs["default"] = p.default.get().val
        else:
            kwargs["required"] = True
        return Opt.some(RegArg(args=p.flag_names, kwargs=kwargs))


class OptionalParamToArg(ParamToArg):
    """Optional parameter to `RegArg` converter."""

    def parse(self, p: Param) -> Opt[RegArg]:
        """Parse a function parameter into `RegArg`."""
        a = p.annotation.get()
        if not (a.wrapped and a.name == "Optional"):
            return Opt.none()
        kwargs = {
            "type": a.type,
            "default": p.default.get().val if p.default.is_some else None,
        }
        return Opt.some(RegArg(args=p.flag_names, kwargs=kwargs))


class ListParamToArg(ParamToArg):
    """List parameter to `RegArg` converter."""

    def parse(self, p: Param) -> Opt[RegArg]:
        """Parse a function parameter into `RegArg`."""
        a = p.annotation.get()
        if not (a.wrapped and a.name in ["list", "List"]):
            return Opt.none()
        kwargs = {
            "type": a.type,
            "action": "store",
            "nargs": "*",
            "default": p.default.get().val if p.default.is_some else [],
        }
        return Opt.some(RegArg(args=p.flag_names, kwargs=kwargs))


@dataclass
class Function:
    """Function wrapper."""

    func: Callable

    @property
    def name(self) -> str:
        """Name of function."""
        return self.func.__name__

    @property
    def doc(self) -> str:
        """Docstring of function."""
        if self.func.__doc__:
            return self.func.__doc__
        return ""

    @cached_property
    def signature(self) -> Signature:
        """Signature of function."""
        return signature(self.func)

    @staticmethod
    def new(func: Callable) -> "Function":
        """Return a new `Function`."""
        return Function(func=func)


class CustomActionProto(Protocol):
    """Protocol that parses given command-line value."""

    @staticmethod
    def parse_flag(value: str) -> Any:
        """Convert value into the value of the implementing type."""


class CustomParamToArg(ParamToArg):
    """Custom argument type to `RegArg` converter."""

    def validate(self, p: Param) -> bool:
        """Parameter type is proper to custom argument type or not."""
        a = p.annotation.get()
        if a.wrapped:  # avoid generic
            return False
        if CustomActionProto in a.type.__bases__:  # extend proto explicitly
            return True
        parse = get_attribute(a.type, "parse_flag")  # has parse_flag() ?
        if not parse.is_some:
            return False
        parse = parse.get()
        if not isfunction(parse):
            return False
        parsef = Function.new(cast(Callable, parse))
        return len(parsef.signature.parameters) == 1

    def parse(self, p: Param) -> Opt[RegArg]:
        """Parse a function parameter into `RegArg`."""
        a = p.annotation.get()

        if not self.validate(p):
            return Opt.none()

        class A(Action):
            def __init__(
                self,
                option_strings,
                dest,
                default=None,
                type=None,
                choices=None,
                required=False,
                help=None,
                metavar=None,
            ):
                super().__init__(
                    option_strings=option_strings,
                    dest=dest,
                    default=default,
                    type=type,
                    choices=choices,
                    required=required,
                    help=help,
                    metavar=metavar,
                )

            def __call__(self, parser, namespace, values, option_string=None):
                setattr(namespace, self.dest, a.type.parse_flag(values))

        kwargs: dict[str, Any] = {
            "action": A,
        }
        if p.default.is_some:
            kwargs["default"] = p.default.get().val
        else:
            kwargs["required"] = True
        return Opt.some(RegArg(args=p.flag_names, kwargs=kwargs))


class RegArgGenerator:
    """Function to command arguments converter."""

    @classmethod
    def generate(cls, f: Function, abbr: bool = False) -> RegArgList:
        """Generate command arguments."""
        return RegArgList([cls.parse(x, abbr) for x in f.signature.parameters.values()])

    @staticmethod
    def parse(parameter: Parameter, abbr: bool = False) -> RegArg:
        """Parse a function parameter as a command argument."""
        param = Param.new(parameter, abbr)
        parsers: list[ParamToArg] = [
            CustomParamToArg(),
            BoolParamToArg(),
            OptionalParamToArg(),
            ListParamToArg(),
            DefaultParamToArg(),
        ]
        for parser in parsers:
            v = parser.parse(param)
            if v.is_some:
                return v.get()
        raise BadTargetException(param)


@dataclass
class CommandGenerator:
    """Function to `Command` converter."""

    func: Function

    @staticmethod
    def new(f: Callable) -> "CommandGenerator":
        """Return a new `CommandGenerator`."""
        if not isfunction(f):
            raise BadTargetException(f"{f} not a function")
        if f.__name__ == "<lambda>":
            raise BadTargetException(f"{f} cannot accept lambda")
        return CommandGenerator(func=Function.new(f))

    def regargs(self, abbr: bool = False) -> RegArgList:
        """Generate `RegArgList`."""
        return RegArgGenerator.generate(self.func, abbr)

    def class_name(self) -> str:
        """Return the name of a class to be generated."""
        return f"pk_generated_{self.func.name}"

    def generate(self, abbr: bool = False) -> type:
        """Generate `Command` class definition."""
        regargs = self.regargs(abbr)
        this = self

        def name() -> str:
            return this.func.name

        def _help(cls) -> str:
            return dedent(this.func.doc).strip()

        def register(cls, parser: ArgumentParser):
            regargs.apply(parser)

        def run(self, args: Namespace):
            vs = vars(args)
            del vs["command"]  # delete unexpected argument
            this.func.func(**vs)

        return type(
            this.class_name(),
            (Command,),
            {
                "name": staticmethod(name),
                "help": classmethod(_help),
                "run": run,
                "register": classmethod(register),
            },
        )


class Wrapper:  # noqa
    """
    Function-based CLI generator.

    Basic usage:

    ```
    from pkommand import Wrapper
    def hello(name: str):
        print(f"hello {name}!")
    w = Wrapper.default()
    w.add(hello)
    w.run()
    # e.g. command-line arguments: --name alice
    # output:
    # hello alice!
    ```

    Parameters:

    Input parameters must be annotated.
    Default value is used as the default value of the flag,
    without default value, the parameter is mandatory.

    `bool` parameter will be a simple flag.

    `typing.Optional` parameter will be the flag with default `None` implicitly.

    `typing.List` and `list` parameters will be the flag collects multiple arguments,
    with default `[]` implicitly.

    Custom type parameter:

    The type that implements `wrapper.CustomActionProto` can be an input parameter annotation.
    For example, comma-separated string list:

    ```
    from pkommand import Wrapper
    from dataclasses import dataclass
    @dataclass
    class StringList:
        values: list[str]
        @staticmethod
        def parse_flag(value: str):
            return StringList(values=value.split(","))
    def hello(names: StringList):
        for name in names.values:
            print(f"hello {name}!")
    w = Wrapper.default()
    w.add(hello)
    w.run()
    # e.g. command-line arguments: --names 'alice,bob'
    # output:
    # hello alice!
    # hello bob!
    ```

    Abbreviated flags are added automatically.
    For example,
    ```
    def f(name: str):
        ...
    ```
    `name` can be specified by `--name` and `-n`.
    ```
    def f(n: str):
        ...
    ```
    `n` can be only specified by `-n` because it cannnot be abbreviated.
    ```
    def f(name: str, next: int):
        ...
    ```
    causes conflict, abbreviations of `name` and `next` are the same `-n`.

    Prevent abbreviations by:
    ```
    w = Wrapper.default(abbr=False)
    ```
    """

    def __init__(self, parser: Parser, abbr: bool = True):
        """Return a new `Wrapper`."""
        self.parser = parser
        self.abbr = abbr

    @staticmethod
    def default(abbr: bool = True) -> "Wrapper":
        """Return a new default `Wrapper`."""
        return Wrapper(Parser(), abbr)

    def add(self, func: Callable):
        """Add new `func` to CLI as a subcommand."""
        klass = CommandGenerator.new(func).generate(self.abbr)
        self.parser.add_command_class(klass)

    def run(self, args=None, namespace=None):
        """Parse arguments and try to execute subcommand."""
        self.parser.run(args=args, namespace=namespace)
