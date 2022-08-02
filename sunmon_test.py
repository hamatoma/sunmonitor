'''
Created on 18.04.2022

@author: wk
'''
import unittest
import datetime
import time
import os.path
from SunMon import Monitor, Statistics


class SimpleRandom:
    def __init__(self):
        self._seed = 101982048390
        self._ixTotal = 0
        self._totals = (5, 10, 24, 26, 50, 100, 20, 60, 150, 200,
                        200, 20, 300, 400, 500, 600, 580, 590, 500, 20,
                        300, 250, 210, 150, 10, 2, 110, 90, 80, 70,
                        20, 0)

    def randomTotal(self) -> float:
        rc = self._totals[self._ixTotal]
        self._ixTotal = (self._ixTotal + 1) % len(self._totals)
        return rc

    def randomInt(self) -> float:
        self._seed = (self._seed * 1103515245 + 12345) % 0xffffffff
        return self._seed

    def randomFloat(self, minValue: float, maxValue: float) -> float:
        value = self.randomInt()
        return minValue + (maxValue - minValue) * value / 0xffffffff


gRand = SimpleRandom()


def gRandom():
    return gRand


class SunMonTest(unittest.TestCase):
    configFile = '/tmp/sunmon_test.conf'
    testDay = datetime.datetime(2022, 2, 3, 0, 0)

    def clearDays(self, monitor: Monitor):
        sql = '''DELETE from days;
'''
        monitor.dbExecute(sql, None)

    def populateOneRow(self, monitor: Monitor, timestamp: int):
        sql = '''INSERT INTO events 
(event_time, event_apower, event_voltage, event_current, event_total, event_temperature, created, createdby) 
VALUES (%s, %s, %s, %s, %s, %s, %s, %s);'
'''
        power = gRandom().randomTotal()
        self._lastTotal += power / 4
        time2 = time.localtime(timestamp)
        timeStr = time.strftime('%Y-%m-%d %H:%M:%S', time2)
        values = (timeStr, power, 230 + gRandom().randomFloat(-10, +10), power / 230, self._lastTotal,
                  60 + gRandom().randomFloat(-10, +20), timeStr, 'unittest')
        monitor.dbExecute(sql, values)

    def populateData(self, monitor: Monitor):
        if not monitor.hasData('events'):
            self._lastTotal = 50000
            startTime = SunMonTest.testDay.timestamp() + 8 * 3600
            for quarter in range(4 * 4):
                self.populateOneRow(monitor, startTime + quarter * 15 * 60)
            self._lastTotal = 0
            start2 = startTime + 16 * 15 * 60
            for quarter in range(4 * 4):
                self.populateOneRow(monitor, start2 + quarter * 15 * 60)

    def setUp(self):
        if not os.path.exists(SunMonTest.configFile):
            with open(SunMonTest.configFile, 'w') as fp:
                fp.write('''# configuration of the unit test
net.domain=localhost
net.port=8081
net.timeout=10
#net.path=/rpc/Switch.GetStatus?id=0
net.path=/status
db.name=appsuntest
db.user=sun
db.code=sun4sun
service.interval=60
''')
        monitor = Monitor()
        monitor.config(SunMonTest.configFile)
        monitor.dbConnect()
        monitor.createTableIfNotExists()
        self.populateData(monitor)
        self.clearDays(monitor)
        monitor.dbClose()

    def testStatisticsPopulateMinMax(self):
        # Format of one row: (event_time, event_total)
        d1 = SunMonTest.testDay.strftime('%Y-%m-%d')
        rows1 = ([f'{d1} 10:33:00', 550.0], [f'{d1} 10:35:00', 100.3], [
                 f'{d1} 10:34:00', 200.3], [f'{d1} 10:36:00', 150.3])
        rows = list(map(lambda x: (datetime.datetime.strptime(
            x[0], '%Y-%m-%d %H:%M:%S'), x[1]), rows1))
        stat = Statistics(rows)
        for row in rows:
            stat.populateMinMax(row[1])
        self.assertEqual(stat.energyMin, 100.3)
        self.assertEqual(stat. energyMax, 550.0)
        stat = Statistics(rows)
        for row in rows[1:]:
            total = row[1]
            stat.populateMinMax(total)
            stat.populateLastTotal(total)
        self.assertEqual(stat.energyMin, 100.3)
        self.assertEqual(stat.energyMax, 200.3)

    def testStatisticspopulatePowerRange(self):
        # Format of one row: (event_time, event_total)
        d1 = SunMonTest.testDay.strftime('%Y-%m-%d')
        rows1 = ([f'{d1} 10:33:00', 590.0], [f'{d1} 10:35:00', 100.3], [f'{d1} 10:39:00', 200.3],
                 [f'{d1} 10:41:00', 150.3], [
                     f'{d1} 10:42:00', 89.2], [f'{d1} 10:43:00', 44.2],
                 [f'{d1} 10:44:00', 26.4], [f'{d1} 10:48:00', 18.5], [
                     f'{d1} 10:49:00', 10.3],
                 [f'{d1} 10:50:00', 5.1], [f'{d1} 10:54:00', 404.2], [f'{d1} 10:59:00', 0.3])
        rows = list(map(lambda x: (datetime.datetime.strptime(
            x[0], '%Y-%m-%d %H:%M:%S'), x[1]), rows1))
        stat = Statistics(rows)
        startTime = rows[0][0].timestamp() - 1
        lastTime = startTime
        for row in rows:
            current = row[0].timestamp()
            timeDiff = int(current - lastTime)
            lastTime = current
            print(f'diff: {timeDiff} apower: {row[1]}')
            stat.populatePowerRange(row[1], timeDiff)
        self.assertEqual(stat.powerValues, [
                         1201, 901, 781, 721, 481, 241, 241, 1, 1])

    def testStatisticsPopulateTimeRange(self):
        # Format of one row: (event_time, event_total)
        d1 = SunMonTest.testDay.strftime('%Y-%m-%d')
        rows1 = ([f'{d1} 07:31:11', 5009.0], [f'{d1} 07:32:12', 5014.2], [f'{d1} 08:39:01', 5020.3],
                 [f'{d1} 09:41:00', 5150.3], [f'{d1} 10:42:00',
                                              5189.2], [f'{d1} 11:43:00', 5244.2],
                 [f'{d1} 12:44:00', 260.1], [
                     f'{d1} 13:48:00', 900], [f'{d1} 15:49:00', 1500],
                 [f'{d1} 16:50:00', 2000], [f'{d1} 17:54:00', 2100], [f'{d1} 18:59:00', 2101])
        rows = list(map(lambda x: (datetime.datetime.strptime(
            x[0], '%Y-%m-%d %H:%M:%S'), x[1]), rows1))
        stat = Statistics(rows)
        for row in rows:
            total = row[1]
            timestamp = row[0].timestamp()
            stat.populateTimeRange(total, timestamp)
            stat.populateMinMax(total)
            if stat.lastDebugMessage != None:
                print('                         ' + stat.lastDebugMessage)
            stat.populateLastTotal(total)
            print(f'{row[0]} {timestamp} total: {total}')
        stat.populateFinish(rows)
        for ix in range(Statistics.limitsHoursMin, Statistics.limitsHoursMax + 3):
            print(f'hour: {ix}: {stat.timeValues[ix]}')
        self.assertEqual(5244.2 - 5009.0 + 2101, stat.energyOfDay)
        self.assertEqual(260.1, stat.energyMin)
        self.assertEqual(5244.2, stat.energyMax)
        values = list(map(lambda x: int(
            x * 10) / 10.0, stat.timeValues[Statistics.limitsHoursMin:Statistics.limitsHoursMax + 2]))
        self.assertEqual(values, [7.7, 47.5, 98.1, 43.0,
                                  38.7, 420.0, 0.0, 836.9, 333.1, 425.4, 84.4, 0.9])

    def testStatisticsPopulate(self):
        # Format of one row: (event_time, event_total)
        d1 = SunMonTest.testDay.strftime('%Y-%m-%d')
        rows1 = ([f'{d1} 07:31:11', 5009.0, 13.7], [f'{d1} 07:32:12', 5014.2, 35.2], [f'{d1} 08:39:01', 5020.3, 98.3],
                 [f'{d1} 09:41:00', 5150.3, 22.7], [f'{d1} 10:42:00',
                                                    5189.2, 302.9], [f'{d1} 11:43:00', 5244.2, 401.8],
                 [f'{d1} 12:44:00', 260.1, 299.7], [f'{d1} 13:48:00',
                                                    900, 592.2], [f'{d1} 15:49:00', 1500, 144.7],
                 [f'{d1} 16:50:00', 2000, 149.5], [f'{d1} 17:54:00', 2100, 322.7], [f'{d1} 18:59:00', 2101, 449.8])
        rows = list(map(lambda x: (datetime.datetime.strptime(
            x[0], '%Y-%m-%d %H:%M:%S'), x[1], x[2]), rows1))
        stat = Statistics(rows)
        doRange = True
        for row in rows:
            total = row[1]
            timestamp = row[0].timestamp()
            stat.populate(row)
            if doRange and not stat.populateTimeRange(total, timestamp):
                doRange = False
            stat.populateLastTotal(total)
        stat.populateFinish(rows)
        values = list(map(lambda x: int(
            x * 10) / 10.0, stat.timeValues[Statistics.limitsHoursMin:Statistics.limitsHoursMax + 2]))
        self.assertEqual(values, [7.7, 47.5, 98.1, 43.0,
                                  38.7, 420.0, 0.0, 836.9, 333.1, 425.4, 84.4, 0.9])
        self.assertEqual(5244.2 - 5009.0 + 2101, stat.energyOfDay)
        self.assertEqual(5244.2, stat.energyMax)
        self.assertEqual(260.1, stat.energyMin)

    def testUpdateOneDay(self):
        # Format of one row: (event_time, event_total)
        d1 = SunMonTest.testDay.strftime('%Y-%m-%d')
        rows1 = ([f'{d1} 07:31:11', 5009.0, 13.7], [f'{d1} 07:32:12', 5014.2, 35.2], [f'{d1} 08:39:01', 5020.3, 98.3],
                 [f'{d1} 09:41:00', 5150.3, 22.7], [f'{d1} 10:42:00',
                                                    5189.2, 302.9], [f'{d1} 11:43:00', 5244.2, 401.8],
                 [f'{d1} 12:44:00', 260.1, 299.7], [f'{d1} 13:48:00',
                                                    900, 592.2], [f'{d1} 15:49:00', 1500, 144.7],
                 [f'{d1} 16:50:00', 2000, 149.5], [f'{d1} 17:54:00', 2100, 322.7], [f'{d1} 18:59:00', 2101, 449.8])
        rows = list(map(lambda x: (datetime.datetime.strptime(
            x[0], '%Y-%m-%d %H:%M:%S'), x[1], x[2]), rows1))
        stat = Statistics(rows)
        for row in rows:
            total = row[1]
            timestamp = row[0].timestamp()
            stat.populate(row)
            stat.populateTimeRange(total, timestamp)
            stat.populateLastTotal(total)
        stat.populateFinish(rows)
        monitor = Monitor()
        monitor.config(SunMonTest.configFile)
        monitor.dbConnect()
        monitor.updateOneDay(datetime.datetime(2022, 2, 3), stat)
        sql = f'''SELECT
  day_id, day_date, day_totalmin, day_totalmax, day_energy,
  day_hour8, day_hour9, day_hour10, day_hour11, day_hour12, day_hour13, day_hour14, day_hour15, day_hour16, day_hour17, day_hourRest, 
  day_energy10, day_energy25, day_energy50, day_energy100, day_energy200, day_energy300, day_energy400, day_energy500, day_energy590
FROM days
WHERE day_date='{d1}';
'''
        rows = monitor.dbSelect(sql)
        self.assertEquals(len(rows), 1)
        row = rows[0]
        self.assertEqual(datetime.date(2022, 2, 3), row[1])
        self.assertEqual(260.1, row[2])
        self.assertEqual(5244.2, row[3])
        self.assertEqual(2336.2, row[4])
        self.assertEqual(7.73799, float(row[5]))
        self.assertEqual(47.5712, row[6])
        self.assertEqual(98.1073, row[7])
        self.assertEqual(43.0131, row[8])
        self.assertEqual(38.7705, row[9])
        self.assertEqual(420.075, row[10])
        self.assertEqual(0.0, row[11])
        self.assertEqual(836.95, row[12])
        self.assertEqual(333.139, row[13])
        self.assertEqual(425.461, row[14])
        self.assertEqual(0.907692, row[15])
        self.assertEqual(41270, row[16])
        self.assertEqual(37550, row[17])
        self.assertEqual(37489, row[18])
        self.assertEqual(33480, row[19])
        self.assertEqual(22560, row[20])
        self.assertEqual(18900, row[21])
        self.assertEqual(11400, row[22])
        self.assertEqual(3840, row[23])
        self.assertEqual(3840, row[24])
        monitor.dbClose()

    def testUpdateDays(self):
        d1 = SunMonTest.testDay.strftime('%Y-%m-%d')
        monitor = Monitor()
        monitor.config(SunMonTest.configFile)
        monitor.dbConnect()
        monitor.updateDays(SunMonTest.testDay,
                           SunMonTest.testDay + datetime.timedelta(days=1))
        sql = f'''SELECT
  day_id, day_date, day_totalmin, day_totalmax, day_energy,
  day_hour8, day_hour9, day_hour10, day_hour11, day_hour12, day_hour13, day_hour14, day_hour15, day_hour16, day_hour17, day_hourRest, 
  day_energy10, day_energy25, day_energy50, day_energy100, day_energy200, day_energy300, day_energy400, day_energy500, day_energy590
FROM days
WHERE day_date='{d1}';
'''
        rows = monitor.dbSelect(sql)
        self.assertEquals(len(rows), 1)
        row = rows[0]
        testDay = SunMonTest.testDay.date()
        self.assertEqual(testDay, row[1])
        row = rows[0]
        self.assertEqual(testDay, row[1])
        self.assertEqual(145, row[2])
        self.assertEqual(50666.2, row[3])
        self.assertEqual(1410.5, row[4])
        self.assertEqual(0, float(row[5]))
        self.assertEqual(27.6, float(row[6]))
        self.assertEqual(82.4, row[7])
        self.assertEqual(180.0, row[8])
        self.assertEqual(375.0, row[9])
        self.assertEqual(497.5, row[10])
        self.assertEqual(155.0, row[11])
        self.assertEqual(70.5, row[12])
        self.assertEqual(0, row[13])
        self.assertEqual(0, row[14])
        self.assertEqual(22.5, row[15])
        self.assertEqual(26100, row[16])
        self.assertEqual(19800, row[17])
        self.assertEqual(18900, row[18])
        self.assertEqual(14400, row[19])
        self.assertEqual(10800, row[20])
        self.assertEqual(7200, row[21])
        self.assertEqual(5400, row[22])
        self.assertEqual(4500, row[23])
        self.assertEqual(1800, row[24])
        monitor.dbClose()


if __name__ == "__main__":
    unittest.main()
