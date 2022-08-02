'''
Created on 28.07.2022

@author: wk
'''
import unittest
import os.path
from SilentLog import SilentLog


class SilentLogTest(unittest.TestCase):
    configurationFile = '/tmp/silentlog.conf'

    def setUp(self):
        if not os.path.exists(SilentLogTest.configurationFile):
            with open(SilentLogTest.configurationFile, 'w') as fp:
                fp.write('''# Example file
silent.log.max.errors=25
silent.log.max.messages=250
''')

    def testHasError(self):
        log = SilentLog()
        self.assertFalse(log.hasErrors())
        log.error('e1')
        self.assertTrue(log.hasErrors())

    def testHasMessages(self):
        log = SilentLog()
        self.assertFalse(log.hasMessages())
        log.log('l1')
        self.assertTrue(log.hasMessages())

    def testClearErrors(self):
        log = SilentLog()
        log.error('e1')
        self.assertFalse(log.clearErrors())
        self.assertFalse(log.hasErrors())

    def testClearMessages(self):
        log = SilentLog()
        log.log('l1')
        self.assertFalse(log.clearMessages())
        self.assertFalse(log.hasMessages())

    def testError(self):
        log = SilentLog()
        log.error('e1')
        log.error('e2')
        self.assertEquals(len(log.errorsAsList()), 2)
        self.assertEquals(log.errorsAsList()[0], '+++ e1')
        self.assertEquals(log.errorsAsList()[1], '+++ e2')

    def testLog(self):
        log = SilentLog()
        log.log('l1')
        log.log('l2')
        self.assertEquals(len(log.messagesAsList()), 2)
        self.assertEquals(log.messagesAsList()[0], 'l1')
        self.assertEquals(log.messagesAsList()[1], 'l2')

    def testErrorAsString(self):
        log = SilentLog()
        log.error('e1')
        log.error('error2')
        self.assertEquals(log.errorsAsString(), '+++ e1\n+++ error2')

    def testMessagesAsString(self):
        log = SilentLog()
        log.log('m1')
        log.log('msg2')
        self.assertEquals(log.messagesAsString(), 'm1\nmsg2')

    def testSilentLogConfiguration(self):
        log = SilentLog()
        log.silentLogConfiguration({'log.max.errors': '25',
                                    'log.max.messages': '250'
                                    })
        self.assertEqual(log._maxErrors, 25)
        self.assertEqual(log._maxMessages, 250)

    def testSilentLogConfigurationError(self):
        log = SilentLog()
        log.silentLogConfiguration({'log.max.errors': 'not-a-number'})
        self.assertEqual(log._maxErrors, 100)
        self.assertEqual(log.errorsAsString(
        ), '+++ configuration variable log.max.errors is not an integer: not-a-number')

    def testExample(self):
        self.assertTrue(SilentLog.examples().find('log.max.errors') >= 0)
