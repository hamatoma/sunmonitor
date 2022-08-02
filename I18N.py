'''
Created on 28.07.2022

@author: wk
'''
import os.path
from Configuration import Configuration
from Snippets import Snippets


class I18N (Configuration):
    '''Manages translated texts.
    '''

    def __init__(self, languages=['de', 'en']):
        '''Constructor.
        @param languages: a list of supported languages, e.g. ['de', 'en']
        '''
        Configuration.__init__(self)
        self.language = languages[0]
        self._languages = languages
        self.formatDate = '%d.%m.%Y'
        self.formatDateTime = '%d.%m.%Y %H:%M:%S'
        self.separatorDate = '.'

    def findFile(self, prefix: str):
        rc = None
        for lang in ('current ' + self._languages).split(' '):
            filename = f'{prefix}.{lang}'
            if os.path.exists(filename):
                self.language = lang
                rc = filename
                break
        if rc == None:
            self.error(f'file {prefix}.en does not exist')
        return rc

    def read(self, prefix: str):
        filename = self.findFile(prefix)
        if filename != None:
            super().read(filename)

    def replaceI18n(self, text: str) -> str:
        rc = Snippets.replaceI18n(text, self._variables)
        return rc

    def translate(self, key: str) -> str:
        rc = self.asString(key)
        return rc

    def variables(self):
        return self._variables
