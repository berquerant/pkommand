from contextlib import redirect_stdout
from dataclasses import dataclass
from inspect import signature
from io import StringIO
from typing import Any, Callable, List, Optional

import pytest

import pkommand.container as c
import pkommand.wrapper as wrapper


def t_default_no_default(a: int):
    pass


def t_default_with_default(a: int = 1):
    pass


@pytest.mark.parametrize(
    "f,want",
    [
        (t_default_no_default, c.Opt.none()),
        (t_default_with_default, c.Opt.some(1)),
    ],
)
def test_default(f: Callable, want: c.Opt):
    s = signature(f)
    p = list(s.parameters.values())[0]
    got = wrapper.Default.new(p)
    assert got.and_then(lambda x: x.val) == want, got


def t_annotation_no_annotation(a):
    pass


def t_annotation_with_annotation(a: bool):
    pass


def t_annotation_with_alias_annotation_list(a: list[int]):
    pass


def t_annotation_with_alias_annotation_glist(a: List[int]):
    pass


def t_annotation_with_alias_annotation_optional(a: Optional[int]):
    pass


@pytest.mark.parametrize(
    "f,want",
    [
        (
            t_annotation_no_annotation,
            c.Opt.none(),
        ),
        (
            t_annotation_with_annotation,
            c.Opt.some(("bool", bool)),
        ),
        (
            t_annotation_with_alias_annotation_list,
            c.Opt.some(("list", int)),
        ),
        (
            t_annotation_with_alias_annotation_glist,
            c.Opt.some(("List", int)),
        ),
        (
            t_annotation_with_alias_annotation_optional,
            c.Opt.some(("Optional", int)),
        ),
    ],
)
def test_annotation(f: Callable, want: c.Opt):
    s = signature(f)
    p = list(s.parameters.values())[0]
    got = wrapper.Annotation.new(p)
    assert got.and_then(lambda x: x.name) == want.and_then(lambda x: x[0]), got
    assert got.and_then(lambda x: x.type) == want.and_then(lambda x: x[1]), got


def zero_command():
    """zero_help"""
    print("zero_run")


def unary_command(target: int):
    """unary_help"""
    print(f"unary_run {target}")


def bool_command(b1: bool, b2: bool = False, b3: bool = True):
    """bool_help"""
    print(f"bool_run {b1} {b2} {b3}")


def optional_command(o1: Optional[int], o2: Optional[int] = 1):
    """optional_help"""
    print(f"optional_run {o1} {o2}")


def list_command(l1: list[int], l2: list[int] = [1]):
    """list_help"""
    print(f"list_run {l1} {l2}")


@dataclass
class StringList:
    values: list[str]

    @staticmethod
    def parse_flag(value: str) -> Any:
        return StringList(values=value.split(","))


def custom_command(c1: StringList, c2: StringList = StringList(values=[])):
    """custom_help"""
    print(f"custom_run {c1} {c2}")


@pytest.mark.parametrize(
    "title,func,args,want",
    [
        (
            "custom run",
            custom_command,
            ["custom_command", "--c1", "1,2,3"],
            "custom_run StringList(values=['1', '2', '3']) StringList(values=[])\n",
        ),
        (
            "list run",
            list_command,
            ["list_command", "--l1", "1", "2", "--l2", "9"],
            "list_run [1, 2] [9]\n",
        ),
        (
            "list run default",
            list_command,
            ["list_command"],
            "list_run [] [1]\n",
        ),
        (
            "optional run",
            optional_command,
            ["optional_command", "--o1", "21", "--o2", "1"],
            "optional_run 21 1\n",
        ),
        (
            "optional run default",
            optional_command,
            ["optional_command"],
            "optional_run None 1\n",
        ),
        (
            "bool run",
            bool_command,
            ["bool_command", "--b2"],
            "bool_run False True True\n",
        ),
        (
            "bool run default",
            bool_command,
            ["bool_command", "--b1"],
            "bool_run True False True\n",
        ),
        (
            "unary run",
            unary_command,
            ["unary_command", "--target", "10"],
            "unary_run 10\n",
        ),
        (
            "zero help help",
            zero_command,
            ["help", "help"],
            """usage: pytest help [subcommand]

positional arguments:
  subcommand

show help and exit
""",
        ),
        (
            "zero help",
            zero_command,
            ["help"],
            """usage: pytest {help,zero_command} ...

positional arguments:
  {help,zero_command}
    help               show help and exit
    zero_command       zero_help
""",
        ),
        (
            "zero subhelp",
            zero_command,
            ["help", "zero_command"],
            """usage: pytest zero_command

zero_help
""",
        ),
        (
            "zero run",
            zero_command,
            ["zero_command"],
            "zero_run\n",
        ),
    ],
)
def test_run(title: str, func: Callable, args: list[str], want: str):
    w = wrapper.Wrapper.default()
    w.add(func)

    def f():
        b = StringIO()
        with redirect_stdout(b):
            w.run(args=args)
        return b.getvalue()

    assert want == f(), title
