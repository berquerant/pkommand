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
    prepare().run(["help"])
    assert (
        """usage: pytest {help,hello} ...

positional arguments:
  {help,hello}
    help        show help and exit
    hello       say hello
"""
        == capsys.readouterr().out
    )

    prepare().run(["help", "hello"])
    assert (
        """usage: pytest hello [--target TARGET]

optional arguments:
  --target TARGET

say hello
"""
        == capsys.readouterr().out
    )

    prepare().run(["hello", "--target", "alice"])
    assert "hello alice!\n" == capsys.readouterr().out
