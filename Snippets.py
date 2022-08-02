'''
Created on 28.07.2022

@author: wk
'''
import re
import StringUtils
from SilentLog import SilentLog


class Snippets (SilentLog):
    '''Manages a pool of strings with names.
    The snippets are stored in a text file.
    Each snippet is preceded by a headline: the name of the snippet followed by a ':'
    '''
    rexprMacro = re.compile(r'~([a-zA-Z_0-9.-]+)~')
    rexprI18nMacro = re.compile(r'i18n\(([a-zA-Z_0-9.-]+)\)')

    def __init__(self, fileSnippets: str):
        '''Constructor.
        @param fileSnippets: None or the name of the file containing the snippets
        '''
        SilentLog.__init__(self)
        self._snippets = {}
        if fileSnippets != None:
            self.readSnippets(fileSnippets)

    def asString(self, name: str, i18nData=None, macros=None) -> str:
        '''Returns the snippet given by its name.
        @param name: the snippet's name
        @return: the snippet as one string
        '''
        rc = None
        if name not in self._snippets:
            self.error(f'unknown snippet: {name}')
        else:
            rc = self._snippets[name]
            if i18nData != None:
                rc = Snippets.replaceI18n(rc, i18nData)
            if macros != None:
                rc = Snippets.replace(rc, macros)
        return rc

    def readSnippets(self, filename: str):
        '''Reads the snippets from a file.
        @param filename: the name of the file
        '''
        rexprLabel = re.compile(r'^([A-Z_0-9]+):')
        with open(filename, 'r') as fp:
            lines = []
            lastName = None
            for line in fp:
                matcher = rexprLabel.match(line)
                if matcher == None:
                    lines.append(line)
                else:
                    if lastName != None:
                        if len(lines) > 0 and lines[len(lines) - 1].strip() == '':
                            lines = lines[0:len(lines) - 1]
                        self._snippets[lastName] = ''.join(lines)
                    lastName = matcher.group(1)
                    lines = []
            if lastName != None:
                if len(lines) > 0 and lines[len(lines) - 1].strip() == '':
                    lines = lines[0:len(lines) - 1]
                self._snippets[lastName] = ''.join(lines)

    @staticmethod
    def replace(text: str, macros, regExpr=None):
        '''Replaces all macros in a given text with values given by a map.
        The syntax of the macro: ~name~
        @param text: the text to inspect
        @param macros: the map with the (name, replacement) tuples
        @return: the text with the replaced macros
        '''
        if regExpr == None:
            regExpr = Snippets.rexprMacro
        if text == None:
            rc = None
        else:
            rc = ''
            lastEnd = 0
            for matcher in regExpr.finditer(text):
                name = matcher.group(1)
                if name in macros:
                    rc += text[lastEnd:matcher.start()] + StringUtils.toString(macros[name], None, 2)
                    lastEnd = matcher.end()
            if lastEnd == 0:
                rc = text
            else:
                rc += text[lastEnd:]
        return rc

    @staticmethod
    def replaceI18n(text: str, macros):
        '''Replaces all i18n macros in a given text with values given by a map.
        The syntax of the macro: i18n(name)
        @param text: the text to inspect
        @param map: the map with the (name, translation) tuples 
        @return: the text with the replaced macros
        '''
        rc = Snippets.replace(text, macros, Snippets.rexprI18nMacro)
        return rc
