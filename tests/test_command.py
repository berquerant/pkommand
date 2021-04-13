import unittest

import pkommand.command as command


class PseudoCommand(command.Command):
    @staticmethod
    def name():
        return "pseudo_command_name"

    @classmethod
    def help(cls):
        pass

    def run(self, _):
        pass

    @classmethod
    def register(cls, _):
        pass


class TestCommandClassDict(unittest.TestCase):
    def test_set_success(self):
        pcname = PseudoCommand.name()
        ccd = command.CommandClassDict()
        self.assertIsNone(ccd.get(pcname))
        self.assertIsNone(ccd.get_instance(pcname))
        self.assertEqual(ccd.keys(), [])
        ccd.set(PseudoCommand)
        self.assertTrue(ccd.get(pcname) is PseudoCommand)
        self.assertTrue(isinstance(ccd.get_instance(pcname), PseudoCommand))
        self.assertEqual(ccd.keys(), [pcname])

    def test_set_failure(self):
        class C:
            pass

        with self.assertRaises(TypeError):
            command.CommandClassDict().set(C)
