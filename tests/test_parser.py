from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

import pytest

import pkommand.parser as parser


def test_no_subcommands():
    with pytest.raises(parser.NoSubcommandsException):
        parser.Parser().run()


class ZeroCommand(parser.Command):
    @staticmethod
    def name():
        return "zero"

    @classmethod
    def help(cls):
        return "zero_help"

    def run(self, _):
        print("zero_run")

    @classmethod
    def register(cls, _):
        pass


class UnaryCommand(parser.Command):
    @staticmethod
    def name():
        return "unary"

    @classmethod
    def help(cls):
        return "unary_help"

    def run(self, args):
        print("unary_run {}".format(args.target))

    @classmethod
    def register(cls, p):
        p.add_argument("--target", type=int, action="store", help="target_help")


def test_default_run_exception():
    p = parser.Parser()
    p.add_command_class(UnaryCommand)
    with pytest.raises(parser.NoDefaultRunException):
        p.run(args=[])


def test_parse_exception():
    p = parser.Parser()
    p.add_command_class(UnaryCommand)
    b = StringIO()
    with redirect_stderr(b), pytest.raises(SystemExit):
        p.run(args=["unary", "--target", "TARGET"])
    assert (
        """argument --target: invalid int value: 'TARGET'
usage: pytest [-h] {unary} ...

positional arguments:
  {unary}
    unary     unary_help

optional arguments:
  -h, --help  show this help message and exit
"""
        == b.getvalue()
    )


@pytest.mark.parametrize(
    "title,cmds,args,want_output,want_exc",
    [
        (
            "zero help",
            [ZeroCommand],
            ["-h"],
            """usage: pytest [-h] {zero} ...

positional arguments:
  {zero}
    zero      zero_help

optional arguments:
  -h, --help  show this help message and exit
""",
            SystemExit,
        ),
        (
            "zero subhelp",
            [ZeroCommand],
            ["zero", "-h"],
            """usage: pytest zero [-h]

optional arguments:
  -h, --help  show this help message and exit
""",
            SystemExit,
        ),
        (
            "zero run",
            [ZeroCommand],
            ["zero"],
            "zero_run\n",
            None,
        ),
        (
            "zero+unary help",
            [ZeroCommand, UnaryCommand],
            ["-h"],
            """usage: pytest [-h] {zero,unary} ...

positional arguments:
  {zero,unary}
    zero        zero_help
    unary       unary_help

optional arguments:
  -h, --help    show this help message and exit
""",
            SystemExit,
        ),
        (
            "zero+unary zero subhelp",
            [ZeroCommand, UnaryCommand],
            ["zero", "-h"],
            """usage: pytest zero [-h]

optional arguments:
  -h, --help  show this help message and exit
""",
            SystemExit,
        ),
        (
            "zero+unary unary subhelp",
            [ZeroCommand, UnaryCommand],
            ["unary", "-h"],
            """usage: pytest unary [-h] [--target TARGET]

optional arguments:
  -h, --help       show this help message and exit
  --target TARGET  target_help
""",
            SystemExit,
        ),
        (
            "zero+unary zero run",
            [ZeroCommand, UnaryCommand],
            ["zero"],
            "zero_run\n",
            None,
        ),
        (
            "zero+unary unary run",
            [ZeroCommand, UnaryCommand],
            ["unary", "--target", "1"],
            "unary_run 1\n",
            None,
        ),
    ],
)
def test_run_successfully(title, cmds, args, want_output, want_exc):
    p = parser.Parser()
    for c in cmds:
        p.add_command_class(c)

    def f():
        b = StringIO()
        with redirect_stdout(b):
            if not want_exc:
                p.run(args=args)
            else:
                with pytest.raises(want_exc):
                    p.run(args=args)
        return b.getvalue()

    assert want_output == f(), title
