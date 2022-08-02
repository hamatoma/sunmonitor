'''
Created on 28.07.2022

@author: wk
'''
import unittest
import os.path
from Snippets import Snippets


class SnippetsTest(unittest.TestCase):
    snippetFile = '/tmp/snippets_test.html'

    def setUp(self):
        if not os.path.exists(SnippetsTest.snippetFile):
            with open(SnippetsTest.snippetFile, 'w') as fp:
                fp.write('''SNIPPET_MAIN:
<!DOCTYPE html>
<html lang="en" data-url="greenlab.infeos"><head>
<body>
~BODY~
</body>

SNIPPET_BODY:
<h1>Hello World</h1>

SNIPPET_EMPTY:

END:
''')

    def testAsString(self):
        snippets = Snippets(SnippetsTest.snippetFile)
        self.assertEqual(snippets.asString('SNIPPET_MAIN'), '''<!DOCTYPE html>
<html lang="en" data-url="greenlab.infeos"><head>
<body>
~BODY~
</body>
''')
        self.assertEqual(snippets.asString('SNIPPET_BODY'), '''<h1>Hello World</h1>
''')
        self.assertEqual(snippets.asString('SNIPPET_EMPTY'), '')

    def testReplace(self):
        macros = {'m1': 'YY', 'n.2': 'X'}
        self.assertEqual(Snippets.replace(
            '~m1~~n.2~abc~n-2~ ~a~ ~= 4', macros), 'YYXabc~n-2~ ~a~ ~= 4')
        self.assertIsNone(Snippets.replace(None, macros))
        self.assertEqual(Snippets.replace('', macros), '')
        self.assertEqual(Snippets.replace('abc', {}), 'abc')

    def testReplaceI18n(self):
        macros = {'m1': 'YY', 'n.2': 'X'}
        self.assertEqual(Snippets.replaceI18n(
            'i18n(m1)i18n(n.2)abci18n(n-2) ~a~ ~= 4', macros), 'YYXabci18n(n-2) ~a~ ~= 4')
        self.assertIsNone(Snippets.replaceI18n(None, macros))
        self.assertEqual(Snippets.replaceI18n('', macros), '')
        self.assertEqual(Snippets.replaceI18n('abc', {}), 'abc')
