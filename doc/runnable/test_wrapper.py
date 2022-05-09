import pkommand


def hello(target: str):
    """say hello"""
    print(f"hello {target}!")


def prepare():
    w = pkommand.Wrapper.default()
    w.add(hello)
    return w


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
        """usage: pytest hello --target TARGET

options:
  --target TARGET

say hello
"""
        == capsys.readouterr().out
    )

    prepare().run(["hello", "--target", "alice"])
    assert "hello alice!\n" == capsys.readouterr().out
