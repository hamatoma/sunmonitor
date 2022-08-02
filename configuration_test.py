'''
Created on 28.07.2022

@author: wk
'''
import unittest
import os.path
import datetime
from Configuration import Configuration


class ConfigurationTest(unittest.TestCase):
    configurationFile = '/tmp/conf.cunit.conf'

    def setUp(self):
        if not os.path.exists(ConfigurationTest.configurationFile):
            with open(ConfigurationTest.configurationFile, 'w') as fp:
                fp.write('''# Example file

key=123
key.sub.key=abc
word-subword=xyz
count.first=1234
reference=~{key} key: ~{key}
verbose=TruE
debug=yEs
no=nO
nix=FAlse
first=1.9.2022
next=2022-07-23
wrong=2022-13-33
''')

    def testAsString(self):
        config = Configuration(ConfigurationTest.configurationFile)
        self.assertEqual(config.asString('key'), '123')
        self.assertEqual(config.asString('key.sub.key'), 'abc')
        self.assertEqual(config.asString('word-subword'), 'xyz')

    def testAsStringWithMacro(self):
        config = Configuration(ConfigurationTest.configurationFile)
        self.assertEqual(config.asString('reference'), '123 key: 123')

    def testAsStringWithDefault(self):
        config = Configuration(ConfigurationTest.configurationFile)
        self.assertEqual(config.asString('missing', 'not found'), 'not found')
        self.assertEqual(config.asString('missing'), 'missing')

    def testAsInt(self):
        config = Configuration(ConfigurationTest.configurationFile)
        self.assertEqual(config.asString('key'), '123')
        self.assertEqual(config.asString('key.sub.key'), 'abc')
        self.assertEqual(config.asString('word-subword'), 'xyz')

    def testHasKey(self):
        config = Configuration(ConfigurationTest.configurationFile)
        self.assertTrue(config.hasKey('key.sub.key'))
        self.assertFalse(config.hasKey('missing'))

    def testAsBool(self):
        config = Configuration(ConfigurationTest.configurationFile)
        self.assertTrue(config.asBool('verbose'))
        self.assertTrue(config.asBool('debug'))
        self.assertFalse(config.asBool('no'))
        self.assertFalse(config.asBool('nix'))

    def testAsBoolError(self):
        config = Configuration(ConfigurationTest.configurationFile)
        self.assertIsNone(config.asBool('missing'))
        self.assertTrue(config.asBool('missing', True))
        self.assertFalse(config.asBool('missing', False))
        self.assertFalse(config.clear())
        self.assertIsNone(config.asBool('key'))
        self.assertEqual(config.errorsAsString(
        ), '+++ key is not a boolean value[true, yes, false, no]: 123')

    def testAsDate(self):
        config = Configuration(ConfigurationTest.configurationFile)
        self.assertEqual(config.asDate('first'), datetime.date(2022, 9, 1))
        self.assertEqual(config.asDate('next'), datetime.date(2022, 7, 23))
        date1 = datetime.date(2022, 8, 7)
        self.assertEqual(config.asDate('missing', date1), date1)

    def testAsDateWithErrors(self):
        config = Configuration(ConfigurationTest.configurationFile)
        self.assertIsNone(config.asDate('key'))
        self.assertEqual(config.errorsAsString(),
                         '+++ not a date (yyyy-mm-dd or dd.mm.yyyy): 123')
        config.clear()
        self.assertIsNone(config.asDate('wrong'))
        self.assertEqual(config.errorsAsString(
        ), '+++ wrong date ((yyyy-mm-dd or dd.mm.yyyy): 2022-13-33')
