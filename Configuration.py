'''
Created on 28.07.2022

@author: wk
'''
import re
import os.path
import datetime
from Snippets import Snippets
from SilentLog import SilentLog


class Configuration (SilentLog):
    '''Manages translated texts.
    '''
    rexprMacro = re.compile(r'~\{([a-zA-Z0-9.-]+)\}')
    rexprVariable = re.compile(r'^([a-zA-Z0-9.-]+)\s*=\s*(.*)')

    def __init__(self, filename: str=None):
        '''Constructor.
        @param filename: None of the name of the configuration file 
        '''
        SilentLog.__init__(self)
        self._filename = filename
        self.errors = []
        self._variables = {}
        if filename != None:
            self.read(filename)
            self.silentLogConfiguration(self._variables)

    def asBool(self, key, defaultValue: bool=None) -> bool:
        '''Returns the value of a configuration variable given by its key as a boolean.
        @param key: the key of the variable
        @param defaultValue: if the variable does not exist or the value is not a boolean this value will be returned
        @return the value of the variable with the given key or the defaultValue on error
        '''
        value = self.asString(key) if self.hasKey(key) else None
        if value == None:
            rc = defaultValue
        else:
            value = value.lower()
            if value == 'true' or value == 't' or value == 'yes' or value == 'y':
                rc = True
            elif value == 'false' or value == 'f' or value == 'no' or value == 'n':
                rc = False
            else:
                self.error(
                    f'{key} is not a boolean value[true, yes, false, no]: {value}')
                rc = defaultValue
        return rc

    def asDate(self, key, defaultValue: datetime.date=None) -> datetime.date:
        '''Returns the value of a configuration variable given by its key as a date.
        @param key: the key of the variable
        @param defaultValue: if the variable does not exist or the value is not a date this value will be returned
        @return the value of the variable with the given key or the defaultValue on error
        '''
        rc = defaultValue
        value = self.asString(key) if self.hasKey(key) else None
        if value != None:
            separator = '.' if value.find('.') > 0 else '-'
            parts = value.split(separator)
            if len(parts) != 3:
                self.error(f'not a date (yyyy-mm-dd or dd.mm.yyyy): {value}')
            else:
                try:
                    if len(parts[0]) == 4:
                        rc = datetime.date(
                            int(parts[0]), int(parts[1]), int(parts[2]))
                    elif len(parts[2]) == 4:
                        rc = datetime.date(
                            int(parts[2]), int(parts[1]), int(parts[0]))
                    else:
                        self.error(
                            f'wrong date ((yyyy-mm-dd or dd.mm.yyyy): {value}')
                    if rc == None:
                        self.error(
                            f'wrong date ((yyyy-mm-dd or dd.mm.yyyy): {value}')
                        rc = defaultValue
                except ValueError:
                    self.error(
                        f'wrong date ((yyyy-mm-dd or dd.mm.yyyy): {value}')
                    rc = defaultValue
        return rc

    def asInt(self, key, defaultValue: int=-1) -> int:
        '''Returns the value of a configuration variable given by its key as an integer.
        @param key: the key of the variable
        @param defaultValue: if the variable does not exist or the value is not an integer this value will be returned
        @return the value of the variable with the given key or the defaultValue on error
        '''
        value = self.asString(key) if self.hasKey(key) else None
        if value == None:
            rc = defaultValue
        else:
            try:
                rc = int(value)
            except ValueError:
                rc = defaultValue
        return rc

    def asString(self, key: str, defaultValue: str=None) -> str:
        '''Returns the value of a configuration variable given by its key.
        @param key: the key of the variable
        @return: if the variable does not exist: defaultValue or (if that does not exist) the key
            otherwise: the value of the variable
        '''
        rc = self._variables[key] if key in self._variables else (
            key if defaultValue == None else defaultValue)
        return rc

    def hasKey(self, key):
        '''Tests whether there is a given key.
        @param key: the key to test
        @return True: the key exists
        '''
        return key in self._variables

    def read(self, filename: str):
        '''Reads the configuration from a file.
        @param filename: the name of the file
        '''
        if not os.path.exists(filename):
            self.error(f'missing {filename}')
        else:
            with open(filename, 'r') as fp:
                lineNo = 0
                count = 0
                for line in fp:
                    lineNo += 1
                    if line.startswith('#') or line.strip() == '':
                        continue
                    matcher = Configuration.rexprVariable.match(line)
                    if matcher == None:
                        self.error(
                            f'{filename}-{lineNo}: illegal input: {line}')
                    else:
                        count += 1
                        name = matcher.group(1)
                        value = matcher.group(2)
                        if name in self._variables:
                            self.error(
                                f'{filename}-{lineNo}: key is already defined: {name}')
                        else:
                            self._variables[name] = Snippets.replace(
                                value, self._variables, Configuration.rexprMacro)
                self.log(f'{filename} contains {count} variable(s)')
