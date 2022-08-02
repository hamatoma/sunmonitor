'''
Created on 21.07.2022

@author: wk
'''
import mysql.connector
from SilentLog import SilentLog
from Configuration import Configuration


class MyDb (SilentLog):
    def __init__(self):
        '''Constructor.
        '''
        SilentLog.__init__(self, 100)
        self._host = 'localhost'
        self._dbName = 'appsunmonitor'
        self._dbUser = 'sunx'
        self._dbCode = 'sun4suny'
        self._connection = None
        self._cursor = None
        self._autocommit = True

    def _dbConfigOne(self, name: str, configuration: Configuration, defaultValue: str=None) -> str:
        '''Handles one configuration variable.
        @param name: the variable's name
        @param configuration: the configuration manager
        @param defaultValue: this value is used if the variable does not exist or an error has occurred
        @return: the value of the variable
        '''
        rc = defaultValue
        if not configuration.hasKey(name):
            if defaultValue == None:
                self.error(f'missing {name}')
        else:
            rc = configuration.asString(name, defaultValue)
        return rc

    def dbConfig(self, configuration: Configuration) -> bool:
        '''Gets the variables associated to the database from the configuration data.
        @param configuration: the configuration manager
        @return True: all needed data found 
            False: missing some needed configuration
        '''
        self._dbName = self._dbConfigOne('db.name', configuration)
        self._dbUser = self._dbConfigOne('db.user', configuration)
        self._dbHost = self._dbConfigOne('db.host', configuration, 'localhost')
        self._dbCode = self._dbConfigOne('db.code', configuration)
        found = self._dbName != None and self._dbUser != None and self._dbCode != None
        return found

    def dbConnect(self):
        '''Connects the database with the login data from the configuration.
        '''
        self._connection = mysql.connector.connect(host=self._host, user=self._dbUser, password=self._dbCode,
                                                   database=self._dbName, autocommit=self._autocommit)
        if self._connection == None:
            self.error('cannot connect to db')
        else:
            self.log(f'connected to {self._dbName}')

    def dbClose(self):
        '''Closes the connection.
        '''
        self.debug(f'closing {self._dbName}')
        self.dbCloseCursor()
        if self._connection != None:
            self._connection.close()
            self._connection = None

    def dbCloseCursor(self):
        '''Closes the cursor and delete that.
        '''
        self.debug('dbCloseCursor')
        if self._cursor != None:
            self._cursor.close()
            # self._connection.consume_results()
            self._cursor = None

    def dbCommit(self):
        '''Commits the last transaction.
        '''
        self.debug('dbCommit')
        if not self._autocommit:
            try:
                self._connection.commit()
            except Exception as exc:
                self.debug(f'commit failed: {exc}')
        self.dbCloseCursor()

    def dbExecute(self, sql: str, values=None):
        '''Executes a SQL statement without result: INSERT, UPDATE, DELETE...
        @param sql: the SQL statement
        @param values: None or the positional parameters
        '''
        self.debug('dbExecute ' + sql[0:20])
        if self._cursor == None:
            if not self._connection.is_connected():
                self.dbReconnect()
            self._cursor = self._connection.cursor()
        self._cursor.execute(sql, values)
        self.dbCommit()

    def dbReconnect(self):
        '''Closes a database connection and reopen that.
        '''
        self.debug('reconnecting...')
        self._connection.reconnect()

    def dbSelect(self, sql, values=None):
        '''Executes a SQL statement without result: INSERT, UPDATE, DELETE...
        @param sql: the SQL statement
        @param values: None or the positional parameters
        @return a list of records
        '''
        self.debug('dbSelect ' + sql[0:20])
        if self._cursor == None:
            if not self._connection.is_connected():
                self.dbConnect()
            self._cursor = self._connection.cursor()
        self._cursor.execute(sql, values)
        rc = self._cursor.fetchall()
        self.dbCloseCursor()
        return rc
