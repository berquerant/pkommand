from contextlib import redirect_stderr, redirect_stdout
from io import StringIO

import pytest

import pkommand.parser as parser

# def test_no_subcommands():
#     with pytest.raises(SystemExit):
#         parser.Parser().run()


def test_no_subcommands_default_run():
    b = StringIO()
    with redirect_stdout(b):
        parser.Parser().run([])
    assert (
        b.getvalue()
        == """usage: pytest {help} ...

positional arguments:
  {help}
    help  show help and exit
"""
    )


def test_no_subcommands_on_exception():
    class Parser(parser.Parser):
        def on_parse_exception(self, exc: Exception, file=None):
            raise exc

    with pytest.raises(parser.NoDefaultRunException):
        Parser(default_run=None).run([])


def test_default_run_override():
    class Parser(parser.Parser):
        def default_run(self, args, namespace):
            print("Parser.default_run()")

    b = StringIO()
    with redirect_stdout(b):
        Parser().run([])
    assert b.getvalue() == "Parser.default_run()\n"


def test_default_run_by_option():
    def default_run(parser, args, namespace):
        print("default_run()")

    b = StringIO()
    with redirect_stdout(b):
        parser.Parser(default_run=default_run).run([])
    assert b.getvalue() == "default_run()\n"


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
    p = parser.Parser(default_run=None)
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
usage: pytest {help,unary} ...

positional arguments:
  {help,unary}
    help        show help and exit
    unary       unary_help
"""
        == b.getvalue()
    )


@pytest.mark.parametrize(
    "title,cmds,args,want_output,want_exc",
    [
        (
            "zero help help",
            [ZeroCommand],
            ["help", "help"],
            """usage: pytest help [subcommand]

positional arguments:
  subcommand

show help and exit
""",
            None,
        ),
        (
            "zero help",
            [ZeroCommand],
            ["help"],
            """usage: pytest {help,zero} ...

positional arguments:
  {help,zero}
    help       show help and exit
    zero       zero_help
""",
            None,
        ),
        (
            "zero subhelp",
            [ZeroCommand],
            ["help", "zero"],
            """usage: pytest zero

zero_help
""",
            None,
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
            ["help"],
            """usage: pytest {help,zero,unary} ...

positional arguments:
  {help,zero,unary}
    help             show help and exit
    zero             zero_help
    unary            unary_help
""",
            None,
        ),
        (
            "zero+unary zero subhelp",
            [ZeroCommand, UnaryCommand],
            ["help", "zero"],
            """usage: pytest zero

zero_help
""",
            None,
        ),
        (
            "zero+unary unary subhelp",
            [ZeroCommand, UnaryCommand],
            ["help", "unary"],
            """usage: pytest unary [--target TARGET]

options:
  --target TARGET  target_help

unary_help
""",
            None,
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
