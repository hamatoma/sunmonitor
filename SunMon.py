#! /usr/bin/python3
# install:
# apt python3-pip
# python3 -m pip install mysql-connector-python
from SilentLog import SilentLog
'''
Created on 26.07.2022

@author: Hamatoma
'''
import http.client
import sys
import os.path
import json
import datetime
import re
import time
import math
from MyDb import MyDb
from Configuration import Configuration

VERSION = '2023.03.28.00'


def sunriseDistance(latitude: float, date=None):
    '''Calculates an approximation of the hours from sunrise to the local noon.
    @param: latitude: the east-west coordinate
    @param: longitude: the north-south coordinate
    @param: timezone: the difference between local noon and current time in hours
    @return: the hours between sunrise and noon (or noon and sunset)
    '''
    if date is None:
        date = datetime.datetime.now().date()
    def rad(x): return x*3.141592/180.0
    dayNo = int(datetime.datetime.now().date().strftime('%j'))
    # | (1/15)*arccos[-tan(L)*tan(23.44*sin(360(D+284)/365))] |.
    rc =  abs((1/15)*math.acos(-math.tan(rad(latitude))*math.tan(rad(23.44*math.sin(rad(360*(dayNo+284)/365))))))
    return rc

class Statistics:
    '''Manages the statistics for each day.
    '''
    # the interval bounds (of the energy bands) to observe:
    limitsPower = (10, 25, 50, 100, 200, 300, 400, 500, 590)
    # the first hour of the observed hours: we store the energy produced in the interval of the
    # given hour and the predecessor (hour).
    limitsHoursMin = 8
    # the energy produces after this hour is summarized:
    limitsHoursMax = 18

    def __init__(self, rows):
        '''Constructor.
        @param rows: the database rows delivering the data to store: All data for one day
        Format of one row: (event_time, event_total)
        '''
        self.energyMin = 1E99
        self.energyMax = 0
        self.hourLast = 0
        self.energyOfDay = None
        self.powerValues = list(map(lambda x: 0, Statistics.limitsPower))
        self.lastTotal = float(rows[0][1])
        self.nextHour = None
        self.timeValues = [0 for x in range(24 + 1)]
        self.lastTime = rows[0][0].timestamp()
        self.lboundEnergy = self.lastTotal
        self.totalOfNextHour = self.lboundEnergy
        self.valueLastLimit = self.lboundEnergy
        self.lastDebugMessage = None
        self.totalOfLastBreak = self.lboundEnergy

    @staticmethod
    def datetimeToTimestamp(timeAsString: str) -> int:
        rc = datetime.datetime.strptime(
            timeAsString, '%Y-%m-%d %H:%M:%S').timestamp()
        return rc

    def populate(self, currentTime: int, total: float, aPower: float):
        '''Populates the statistics given by the row.
        @param row: the database row delivering the data to store (one measurement).
        '''
        timeDiff = max(1, currentTime - self.lastTime)
        self.lastTime = currentTime
        self.populatePowerRange(aPower, timeDiff)
        self.populateMinMax(total)

    def populateFinish(self, rows, dayEnergy: float):
        '''Finishes the data collection for the given day.
        @param rows: the database rows delivering the data to store: All data for one day
        @param dayEnergy: the energy of the day.
        '''
        self.timeValues[Statistics.limitsHoursMax + 1] = \
            max(0, rows[len(rows) - 1][1] - self.valueLastLimit)
        useExtern = 'x'.startswith('x')
        if useExtern:
            self.energyOfDay = dayEnergy
        elif self.lboundEnergy == None:
            self.energyOfDay = self.lastTotal - self.totalOfLastBreak
        else:
            if self.energyOfDay == None:
                self.energyOfDay = self.lastTotal - self.totalOfLastBreak
            else:
                self.energyOfDay += self.lastTotal - self.totalOfLastBreak

    def populateLastTotal(self, total):
        self.lastTotal = total

    def populateMinMax(self, total: float):
        '''Maintains the minimum and the maximum of the energy measurements.
        @param total: the energy value of one measurement
        '''
        if total < self.energyMin:
            self. energyMin = total
        if total > self.energyMax:
            self.energyMax = total

    def populatePowerRange(self, aPower: float, timeDiff: int):
        '''Collects the data of the energy ranges.
        @param aPower: the energy value of one measurement
        @param timeDiff: the time in seconds between the previous and the current measurement.
        '''
        for ix in range(len(Statistics.limitsPower)):
            if aPower >= Statistics.limitsPower[ix]:
                self.powerValues[ix] += timeDiff
            else:
                break

    def populateTimeRange(self, total: float, currentTime: int) -> bool:
        '''Fills the array self.timeValues: calculates the energy created in time intervals.
        @param total: the energy value of one measurement
        @param currentTime: the timestamp of the measurement
        @return: False: the loop should be stopped (inspection is finished)
        '''
        rc = True
        done = False
        time1 = time.localtime(currentTime)
        # timeStr = time.strftime('%H:%M:%S', time1)
        currentHour = time1.tm_hour
        if self.nextHour == None:
            self.nextHour = max(currentHour + 1, Statistics.limitsHoursMin)
            self.valueLastLimit = total
        elif total < self.lastTotal:
            if currentHour >= self.nextHour:
                self.timeValues[currentHour] = \
                    max(0, self.lastTotal - self.valueLastLimit)
            else:
                self.timeValues[currentHour + 1] = \
                    max(0, self.lastTotal - self.valueLastLimit)
            if self.energyOfDay == None:
                self.energyOfDay = self.lastTotal - self.totalOfLastBreak
            else:
                self.energyOfDay += self.lastTotal - self.totalOfLastBreak
            self.totalOfLastBreak = 0
            self.lboundEnergy = total
            done = True
        if currentHour >= self.nextHour:
            currentSec = ((time1.tm_hour * 60) + time1.tm_min) * \
                60 + time1.tm_sec
            time2 = time.localtime(self._lastTime)
            lastCurrentSec = ((time2.tm_hour * 60) +
                              time2.tm_min) * 60 + time2.tm_sec
            currentHourSec = currentHour * 3600
            if done:
                totalBound = 0
            elif currentSec - lastCurrentSec != 0:
                totalBound = self.lastTotal + (total - self.lastTotal) * (
                    currentHourSec - lastCurrentSec) / (currentSec - lastCurrentSec)
            else:
                totalBound = total
            self.lastDebugMessage = f'hour: {currentHour} total: {totalBound}'
            if not done:
                self.timeValues[currentHour] = \
                    max(0, totalBound - self.valueLastLimit)
            self.valueLastLimit = totalBound
            self.nextHour += 1
            if self.nextHour > Statistics.limitsHoursMax:
                rc = False
        self._lastTime = currentTime
        return rc


class Monitor (MyDb):
    '''Implements a monitor for a fotovoltaic device:
    Polls the device for status data and store them into a database.
    '''

    def __init__(self):
        '''Constructor.
        '''
        MyDb.__init__(self)
        self.verbose = True
        self._domain = 'sun'
        self._requestPath = '/rpc/Switch.GetStatus?id=0'
        self._port = 81
        self._timeout = 10
        self._configFile = '/etc/sunmonitor/monitor.sun.conf'
        self._wait = 60
        self._from = 5
        self._til = 20
        self._dataStart = datetime.date(2022, 6, 27)
        self._regExprChange = re.compile(r'insert|update', re.I)

    def config(self, configFile: str=None):
        '''Reads the configuration file and sets the internal variables.
        '''
        if configFile == None:
            configFile = self._configFile
        if not os.path.exists(configFile):
            raise Exception(f'+++ missing configuration {configFile}')
        else:
            config = Configuration(configFile)
            self._domain = config.asString('net.domain', self._domain)
            self._requestPath = config.asString('net.path', self._requestPath)
            self._port = config.asInt('net.port', self._port)
            self._timeout = config.asInt('net.timeout', self._timeout)
            self._wait = config.asInt('service.interval', self._wait)
            self._from = config.asInt('service.from', self._from)
            self._til = config.asInt('service.til', self._til)
            self._dataStart = config.asDate('data.start', self._dataStart)
            self.dbConfig(config)

    def createTableIfNotExists(self):
        '''Tests whether the needed tables exist in the database. If not that will be created.
        '''
        records = self.dbSelect('show tables;')
        foundEvents = False
        foundDays = False
        for record in records:
            if record[0] == 'events':
                foundEvents = True
            elif record[0] == 'days':
                foundDays = True
        if not foundEvents:
            self.dbExecute('''create table events (
  event_id int PRIMARY KEY AUTO_INCREMENT,
  event_time datetime,
  event_apower float,
  event_voltage float,
  event_current float,
  event_total float,
  event_temperature float,
  created timestamp null,
  createdby varchar(32)
);''')
        if not foundDays:
            self.dbExecute('''create table days (
  day_id int PRIMARY KEY AUTO_INCREMENT,
  day_date date,
  day_totalmin float,
  day_totalmax float,
  day_energy float,
  day_hour8 float,
  day_hour9 float,
  day_hour10 float,
  day_hour11 float,
  day_hour12 float,
  day_hour13 float,
  day_hour14 float,
  day_hour15 float,
  day_hour16 float,
  day_hour17 float,
  day_hour18 float,
  day_hourRest float,
  day_energy10 int,
  day_energy25 int,
  day_energy50 int,
  day_energy100 int,
  day_energy200 int,
  day_energy300 int,
  day_energy400 int,
  day_energy500 int,
  day_energy590 int,
  created timestamp null,
  createdby varchar(32)
);''')

    def daemon(self, argv):
        '''Starts a never ending HTTP server process.
        @param argv: the command line arguments
        '''
        print(f'sunmonitor started as daemon (version {VERSION})')
        print(f'from: {self._from} until: {self._til}')
        self.verbose = len(argv) >= 1 and argv[0] != '-q'
        self.printMessages = self.verbose
        if self.verbose:
            print("verbose mode")
        while True:
            date = datetime.datetime.now()
            hour = int(date.strftime('%H'))
            if hour >= self._from and hour <= self._til:
                self.status()
            elif self.verbose:
                self.debug("status ignored because of the time range")
            time.sleep(self._wait)

    def example(self):
        '''Creates an example configuration file. 
        '''
        content = f'''# Configuration for sunmonitor
{SilentLog.examples()}
net.domain=192.168.2.44
net.port=80
net.timeout=10
net.path=/rpc/Switch.GetStatus?id=0
#net.path=/status
db.name=appsunmonitor
db.user=sun
db.code=sun4sun
service.interval=60
service.from=5
service.til=21
data.start=2022-06-27
'''
        if not os.path.exists(self._configFile):
            with open(self._configFile, 'w') as fp:
                fp.write(content)
                print(f'written: {self._configFile}')
        else:
            print(content)
            print(f'+++ already exists: {self._configFile}')

    def hasData(self, table: str) -> bool:
        '''Tests whether a given table has data.
        @param table: the table's name
        @return: True: there are data in this table
        '''
        sql = f'SELECT count(*) from {table};'
        rows = self.dbSelect(sql)
        rc = rows[0][0] > 0
        return rc

    def initDb(self, argv):
        '''Initializes the database handling.
        @param argv: program arguments
        @return: the not processed program arguments
        '''
        if len(argv) > 0 and argv[0].startswith('--config='):
            self._configFile = argv[0][9:]
            argv = argv[1:]
        if len(argv) > 0 and argv[0] == '-q':
            self.verbose = False
            argv = argv[1:]
        if self.verbose:
            print(f'= configuration: {self._configFile}')
        self.config()
        self.dbConnect()
        self.createTableIfNotExists()
        return argv

    def initService(self):
        '''Builds the file defining an SystemD service.
        '''
        with open('/etc/systemd/system/sunmonitor.service', 'w') as fp:
            fp.write('''[Unit]
Description=A monitor storing statistic data of a Shelly system.
After=syslog.target
[Service]
Type=simple
User=sun
Group=sun
WorkingDirectory=/opt/sunmonitor
#EnvironmentFile=-/etc/sunmonitor/sunmonitor.env
ExecStart=/opt/sunmonitor/SunMon.py daemon 
#ExecReload=/opt/sunmonitor/SunMon.py reload
SyslogIdentifier=sunmonitor
StandardOutput=syslog
StandardError=syslog
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target

''')

    def status(self):
        '''Requests the status data from a device and stores that into the database.
        '''
        connection = http.client.HTTPConnection(
            self._domain, self._port, self._timeout)
        try:
            connection.request("GET", self._requestPath)
            response = connection.getresponse()
            stringData = response.read()
            data = json.loads(stringData)
            if self.verbose:
                print('time: {}'.format(data['aenergy']['minute_ts']))
                for key in ('apower', 'voltage', 'current'):
                    print("{}: {}".format(key, data[key]))
                print('total: {}'.format(data['aenergy']['total']))
                print('temperature: {}'.format(data['temperature']['tC']))
            self.storeEvent(data['aenergy']['minute_ts'], data['aenergy']['total'], data['apower'],
                            data['voltage'], data['current'], data['temperature']['tC'])
        except:
            self.error(
                f'HTTP connection failed: {self._domain}:{self._port}{self._requestPath}')
        connection.close()

    def storeEvent(self, time: datetime.datetime, total: float, power: float, voltage: float, current: float, temperature: float):
        '''Stores one row of the table "events".
        @param time: the measurement timestamp
        @param total: the summarized energy since the last switch off
        @param power: the current power (W)
        @param voltage: the current voltage (V)
        @param current: the current current (A)
        @param temperature: the current temperature (C) (of the measurement device)
        '''
        now = datetime.datetime.now()
        changed = now.strftime('%Y-%m-%d %H:%M:%S')
        sql = ('INSERT INTO events (event_time, event_total, event_apower, event_voltage, event_current, event_temperature, created, createdby)'
               + ' VALUES (%s, %s, %s, %s, %s, %s, %s, %s);')
        time2 = datetime.datetime.fromtimestamp(
            time).strftime('%Y-%m-%d %H:%M:%S')
        val = (time2, total, power, voltage, current,
               temperature, changed, 'monitor')
        try:
            self.dbExecute(sql, val)
        except Exception as exc:
            self.error(
                f'SQL-insert failed: {exc}')

    def statusWeather(self, verbose=True):
        self._domainWeather = 'api.openweathermap.org'
        connection = http.client.HTTPConnection(
            self._domainWeather, 80, self._timeout)
        connection.request(
            "GET", '/data/2.5/weather?id=2891621&APPID=890c77c362f34ce3fdc327dd810c28e8')
        response = connection.getresponse()
        stringData = response.read()
        data = json.loads(stringData)
        if verbose:
            print('time: {}'.format(data['aenergy']['minute_ts']))

    def updateDays(self, firstDate: datetime.date, lastDate: datetime.date):
        '''Summarizes some data of the table "events" for one day into the table "days".
        @param firstDate: the start of the interval to handle
        @param lastDate: the end of the interval to handle
        @return: a tuple (countTotal, countNew): countTotal is the count of the days in the interval
            countNew is the count of the created rows (in "days"): only not existing days will be created
        '''
        current = firstDate + datetime.timedelta(days=0)
        countNew = 0
        countTotal = 0
        while current < lastDate:
            countTotal += 1
            sql = '''SELECT count(*) FROM days WHERE day_date=%s;'''
            currentDay = current.strftime('%Y-%m-%d')
            recs = self.dbSelect(sql, [currentDay])
            if recs[0][0] == 0:
                #if self.verbose:
                #    print(f'{currentDay}: {len(recs)} record(s)')
                countNew += 1
                currentStr = current.strftime('%Y-%m-%d')
                currentStr2 = currentStr + ' 23:59:59'
                sql = f'''SELECT event_time, event_total, event_apower
FROM events
WHERE 
  event_time >= '{currentStr}' AND event_time <= '{currentStr2}'
ORDER BY event_time;
'''
                rows = self.dbSelect(sql)
                if len(rows) >= 1:
                    statistics = Statistics(rows)
                    checkTimeRange = True
                    dayEnergy = 0
                    minTotal = lastTotal = float(rows[0][1])
                    for row in rows:
                        currentDate = row[0]
                        total = float(row[1])
                        if total < lastTotal:
                            dayEnergy += lastTotal - minTotal
                            minTotal = 0.0
                        lastTotal = total
                        aPower = float(row[2])
                        statistics.populate(
                            currentDate.timestamp(), total, aPower)
                        if checkTimeRange and not statistics.populateTimeRange(total, currentDate.timestamp()):
                            checkTimeRange = False
                        statistics.populateLastTotal(total)
                    dayEnergy += total - minTotal
                    statistics.populateFinish(rows, dayEnergy)
                    self.updateOneDay(currentDate, statistics)
            current += datetime.timedelta(days=1)
        self.debug(f'total: {countTotal} new: {countNew}')
        return (countTotal, countNew)

    def updateOneDay(self, currentDate: datetime.datetime, stat: Statistics):
        '''Summarizes some data of the table "events" for one day into the table "days".
        @param currentDate: the date of the day to handle
        @param stat: the Statistic instance to store the data
        '''
        sql = '''INSERT INTO days
  (day_date, day_totalmin, day_totalmax, day_energy,
  day_hour8, day_hour9, day_hour10, day_hour11, day_hour12, day_hour13, day_hour14, day_hour15, day_hour16, day_hour17, day_hour18, day_hourRest, 
  day_energy10, day_energy25, day_energy50, day_energy100, day_energy200, day_energy300, day_energy400, day_energy500, day_energy590, 
  created, createdby) 
  VALUES(%s, %s, %s, %s, 
  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
  %s, %s, %s, %s, %s, %s, %s, %s, %s,
  %s, %s);
'''
        time2 = currentDate.strftime('%Y-%m-%d')
        changed = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        values = (time2, stat.energyMin, stat.energyMax, stat.energyOfDay,
                  stat.timeValues[Statistics.limitsHoursMin],
                  stat.timeValues[Statistics.limitsHoursMin + 1],
                  stat.timeValues[Statistics.limitsHoursMin + 2],
                  stat.timeValues[Statistics.limitsHoursMin + 3],
                  stat.timeValues[Statistics.limitsHoursMin + 4],
                  stat.timeValues[Statistics.limitsHoursMin + 5],
                  stat.timeValues[Statistics.limitsHoursMin + 6],
                  stat.timeValues[Statistics.limitsHoursMin + 7],
                  stat.timeValues[Statistics.limitsHoursMin + 8],
                  stat.timeValues[Statistics.limitsHoursMin + 9],
                  stat.timeValues[Statistics.limitsHoursMin + 10],
                  stat.timeValues[Statistics.limitsHoursMin + 11],
                  stat.powerValues[0], stat.powerValues[1], stat.powerValues[2], stat.powerValues[3],
                  stat.powerValues[4], stat.powerValues[5], stat.powerValues[6], stat.powerValues[7], stat.powerValues[8],
                  changed, 'statistics')
        self.dbExecute(sql, values)
        if self.verbose:
            print(f'updated: {time2}')

def main(argv):
    mode = 'status' if len(argv) < 1 else argv[0]
    if len(argv) > 0:
        argv = argv[1:]
    monitor = Monitor()
    if mode == 'status':
        monitor.initDb(argv)
        monitor.status()
    elif mode == 'update-days':
        monitor.initDb(argv)
        #until = datetime.date(2023, 3, 20)
        until = datetime.datetime.now().date()
        monitor.updateDays(monitor._dataStart, until)
    elif mode == 'daemon':
        argv = monitor.initDb(argv)
        monitor.daemon(argv)
    elif mode == 'init-service':
        monitor.initService()
    elif mode == 'example':
        monitor = Monitor()
        monitor.example()
    else:
        monitor.error(
            f'unknown mode: {mode} Use status | init-service | example | update-days | daemon')


if __name__ == '__main__':
    main(sys.argv[1:])
