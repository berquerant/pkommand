import pytest

import pkommand


class HelloCommand(pkommand.Command):
    @staticmethod
    def name():
        return "hello"

    @classmethod
    def help(cls):
        return "say hello"

    def run(self, args):
        print("hello {}!".format(args.target))

    @classmethod
    def register(cls, parser):
        parser.add_argument("--target", action="store", type=str)


def prepare():
    p = pkommand.Parser()
    p.add_command_class(HelloCommand)
    return p


def test_run(capsys):
    with pytest.raises(SystemExit):
        prepare().run(["-h"])
    assert (
        """usage: pytest [-h] {hello} ...

positional arguments:
  {hello}
    hello     say hello

optional arguments:
  -h, --help  show this help message and exit
"""
        == capsys.readouterr().out
    )

    with pytest.raises(SystemExit):
        prepare().run(["hello", "-h"])
    assert (
        """usage: pytest hello [-h] [--target TARGET]

optional arguments:
  -h, --help       show this help message and exit
  --target TARGET
"""
        == capsys.readouterr().out
    )

    prepare().run(["hello", "--target", "alice"])
    assert "hello alice!\n" == capsys.readouterr().out
