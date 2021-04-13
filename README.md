# pkommand

pkommand is a small subcommand parser library.

``` python
import pkommand


class Scan(pkommand.Command):
    @staticmethod
    def name():
        return "scan"

    @classmethod
    def help(cls):
        return "do scan"

    def run(self, args):
        print("run scan {}".format(args.table))

    @classmethod
    def register(cls, _):
        pass


class Query(pkommand.Command):
    @staticmethod
    def name():
        return "query"

    @classmethod
    def help(cls):
        return "do query"

    def run(self, args):
        print("run query {} by {}".format(args.table, args.key))

    @classmethod
    def register(cls, parser):
        parser.add_argument("--key", action="store", type=str)


p = pkommand.Parser("cli")
p.add_argument("--table", action="store", type=str)
p.add_command_class(Scan)
p.add_command_class(Query)
p.run()
```

Run like this:

``` shell
% python example.py --table histories scan
run scan histories
% python tmp/hello.py --table histories query --key 1984
run query histories by 1984
```
