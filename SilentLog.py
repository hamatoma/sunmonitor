'''
Created on 29.07.2022

@author: wk
'''


class SilentLog:
    '''Manages a simple message and error handler.
    '''

    def __init__(self, maxMessages=10000, maxErrors=100):
        '''Constructor
        @param maxMessages: the length of the messages list is limited to this value
        @param maxErrors: the length of the error list is limited to this value
        '''
        self._maxErrors = 100
        self._errors = []
        self._maxMessages = maxMessages
        self._logs = []
        self.printErrors = True
        self.printMessages = True
        self.printDebug = False

    def _asBool(self, name: str, variables, defaultValue: bool) -> int:
        '''Returns a configuration variable as a boolean value.
        @param name: the variable's name
        @param variables: the map of the (name, value) tuples
        @param defaultValue: the value of the result if the variable does not exist or an error has occurred
        @return the defaultValue or the value of the variable
        '''
        rc = defaultValue
        if name in variables:
            value = variables[name].lower()
            if value == 'true' or value == 't' or value == 'yes':
                rc = True
            elif value == 'false' or value == 'f' or value == 'no':
                rc = False
            else:
                self.error(
                    f'configuration variable {name} is not a boolean [true, false, yes, no]: {value}')
        return rc

    def _asInt(self, name: str, variables, defaultValue: int) -> int:
        '''Returns a configuration variable as a integer value.
        @param name: the variable's name
        @param variables: the map of the (name, value) tuples
        @param defaultValue: the value of the result if the variable does not exist or an error has occurred
        @return the defaultValue or the value of the variable
        '''
        rc = defaultValue
        if name in variables:
            value = variables[name]
            try:
                rc = int(value)
            except ValueError:
                self.error(
                    f'configuration variable {name} is not an integer: {value}')
                rc = defaultValue
        return rc

    def clear(self):
        '''Clears the errors and the messages.
        '''
        self.clearErrors()
        self.clearMessages()

    def clearErrors(self):
        '''Clears the errors.
        '''
        self._errors = []

    def clearMessages(self):
        '''Clears the messages.
        '''
        self._logs = []

    def error(self, message) -> bool:
        '''Stores an error.
        @param message: the error message
        @return False (for chaining)
        '''
        if len(self._errors) >= self._maxErrors:
            self._errors = self._errors[1:]
        msg = '+++ ' + message
        self._errors.append(msg)
        if self.printErrors:
            print(msg)
        return False

    def errorsAsList(self):
        '''Returns the errors as line list.
        @return: a list of error messages
        '''
        return self._errors

    def errorsAsString(self):
        '''Combines the error lines as a string (separated by newlines).
        @return the errors combined to a string
        '''
        rc = '\n'.join(self._errors)
        return rc

    @staticmethod
    def examples() -> str:
        '''Returns a configuration example.
        @return: a text with a configuration example of the module SilentLog
        '''
        return '''log.max.errors=100
log.max.messages=10000
log.print.messages=True
log.print.errors=True
log.print.debug=False'''

    def debug(self, message):
        if self.printDebug:
            print(message)

    def hasErrors(self) -> bool:
        '''Returns whether there are errors.
        @return: True: There are errors
        '''
        return len(self._errors) > 0

    def hasMessages(self):
        '''Returns whether there are messages.
        @return: True: There are messages
        '''
        return len(self._logs) > 0

    def log(self, message):
        '''Stores a message.
        @param message: the message to store
        @return True (for chaining)
        '''
        if len(self._logs) >= self._maxMessages:
            self._logs = self._logs[1:]
        self._logs.append(message)
        if self.printMessages:
            print(message)
        return True

    def messagesAsList(self):
        '''Returns the messages as line list.
        @return: a list of messages
        '''
        return self._logs

    def messagesAsString(self):
        '''Combines the message lines as a string (separated by newlines).
        @return the errors combined to a string
        '''
        rc = '\n'.join(self._logs)
        return rc

    def silentLogConfiguration(self, variables):
        '''Read the configuration data from a configuration map.
        Note: we cannot use Configuration because of circular include: Configuration is a super class of SilentLog.
        @param variables: the map with (name, value) tuples
        '''
        self._maxErrors = self._asInt(
            'log.max.errors', variables, self._maxErrors)
        self._maxMessages = self._asInt(
            'log.max.messages', variables, self._maxMessages)
        self.printMessages = self._asBool(
            'log.print.messages', variables, self.printMessages)
        self.printErrors = self._asBool(
            'log.print.errors', variables, self.printErrors)
        self.printDebug = self._asBool(
            'log.print.debug', variables, self.printDebug)
