#! /usr/bin/python3
'''
Created on 27.06.2022

@author: Hamatoma
'''
import http.server
import cgi
import datetime
import sys
import SvgDiagram
import os
from MyDb import MyDb
from I18N import I18N
from Snippets import Snippets
from Configuration import Configuration
from SilentLog import SilentLog

VERSION = '2023.03.28.00'


class Service (MyDb):
    _instance = None

    def __init__(self, argv=[]):
        '''Constructor.
        '''
        MyDb.__init__(self)
        self.verbose = True
        self._head = ''
        self._bodyStart = ''
        self._body = ''
        self._form = ''
        self._content = ''
        self.headers = None
        self.fieldDate = ''
        self._configFile = '/etc/sunmonitor/sunmonitor.conf'
        self.fieldMode = 1
        self.fieldFrom = 4
        self.fieldUntil = 22
        self.fieldStart = ''
        self.fieldEnd = ''
        self.bestStartDate = '2023-01-01'
        self.interface = '0.0.0.0'
        self.port = 8080
        self.timeZone = 0
        self.title = 'Sonnenstatistik'
        self.dayTitle = 'Sonnenstatistik (Tag)'
        self.yearTitle = 'Sonnenstatistik (Jahr)'
        self.i18nFilePrefix = 'sunserver.i18n'
        self.i18nLanguages = 'de en'
        self.fileSnippets = 'sunserver.snippets.html'
        if len(argv) > 0 and argv[0].startswith('--config='):
            self._configFile = argv[0][9:]
            argv = argv[1:]
        print(f'configuration: {self._configFile}')
        self.config()
        self.i18n = I18N(self.i18nLanguages)
        self.i18n.read(self.i18nFilePrefix)
        if os.path.exists(self._configFile):
            self.dbConnect()
        self.snippets = Snippets(self.fileSnippets)
        self._titlesSimple = [self.i18n.replaceI18n('i18n(time);1;time;;i18n(count.of.measurements)'),
                              self.i18n.replaceI18n(
                                  'i18n(power) (W);3;;ignore-0;i18n(last.value)'),
                              self.i18n.replaceI18n(
                                  'i18n(energy) (Wh);2;;ignore-0+relative-to-start,last-is-diff;i18n(day.summary)'),
                              self.i18n.replaceI18n('i18n(currency) (A);2;;ignore-0,0-exclude-from-average;i18n(last.value)')]
        self._titlesTotal = [self.i18n.replaceI18n('i18n(time);1;time;;i18n(count.of.measurements)'),
                             self.i18n.replaceI18n(
                                 'i18n(power) (W);3;;ignore-0;i18n(last.value)'),
                             self.i18n.replaceI18n(
                                 'i18n(energy) (Wh);2;;ignore-0+relative-to-start,last-is-diff;i18n(day.summary)'),
                             self.i18n.replaceI18n(
                                 'i18n(currency) (A);2;;ignore-0,0-exclude-from-average;i18n(last.value)'),
                             self.i18n.replaceI18n(
                                 'i18n(voltage) (V);2;;ignore-0,0-exclude-from-average;i18n(last.value)'),
                             self.i18n.replaceI18n('i18n(temperature) (C);2;;ignore-0,0-exclude-from-average;i18n(last.value)')]

    @staticmethod
    def instance():
        '''Returns the singleton instance of Service.
        @return: the only one instance of Service
        '''
        if Service._instance == None:
            Service._instance = Service()
        return Service._instance

    def bestOf(self):
        '''Builds the HTML table with the "best of" data.
        @return: the HTML text of the table
        '''
        sql = f'''SELECT 
  day_date, day_energy
FROM days
WHERE day_date >= '{self.bestStartDate}'
order by day_energy desc
limit 20;
'''
        rowsGood = self.dbSelect(sql)
        sql = f'''SELECT 
  day_date, day_energy
FROM days
WHERE day_date >= '{self.bestStartDate}'
order by day_energy
limit 20;
'''
        rowsBad = self.dbSelect(sql)
        if len(rowsGood) < 1:
            content = self.snippets.asString(
                'HTML_NOT_AVAILABLE', self.i18n.variables())
        else:
            html = ''
            for ix in range(len(rowsGood)):
                if len(html) > 0:
                    html += '\n'
                values = {'dateGood': rowsGood[ix][0].strftime(self.i18n.formatDate),
                          'valGood': f'{rowsGood[ix][1]:.0f}',
                          'dateBad': rowsBad[ix][0].strftime(self.i18n.formatDate),
                          'valBad': f'{rowsBad[ix][1]:.0f}'}
                html += self.snippets.asString(
                    'HTML_BEST_LIST_ROW', None, values)
            content = self.snippets.asString(
                'HTML_BEST_LIST', self.i18n.variables(), {'ROWS': html})
        return content

    def dayToSvg(self, start: str, end: str):
        '''Builds the SVG image from the db data.
        @param start: the start of the interval to display
        @param end: the end of the interval to display
        @returns: the SVG text
        '''
        service = Service.instance()
        words = start.split(' ')
        parts = words[0].split(self.i18n.separatorDate)
        if len(parts) != 3:
            content = ''
        else:
            start2 = f'{parts[2]}-{parts[1]}-{parts[0]} {words[1]}'
            words = end.split(' ')
            parts = words[0].split('.')
            end2 = f'{parts[2]}-{parts[1]}-{parts[0]} {words[1]}'
            sql = '''SELECT unix_timestamp(event_time) as seconds,
  event_apower,event_total,event_current,event_voltage,event_temperature
FROM events 
WHERE event_time>=%s AND event_time <=%s AND event_total > 0.0
ORDER BY event_time, event_id;
'''
            svg = SvgDiagram.Diagram(self.i18n)
            svg.outputFileType = 'no-body'
            if service.fieldMode == 1:
                # title strokeWidth displayType attributes comment
                svg.setTitles(self._titlesSimple)
            else:
                svg.setTitles(self._titlesTotal)
            rows = self.dbSelect(sql, (start2, end2))
            if len(rows) <= 1:
                content = self.snippets.asString('HTML_NOT_AVAILABLE2', self.i18n.variables(), {
                                                 'start': start, 'end': end})
            else:
                firstTime = None
                for row in rows:
                    if firstTime == None:
                        firstTime = row[0]
                    lastTime = row[0] % 86400 / 3600.0 + self.timeZone
                    if service.fieldMode == 1:
                        svg.addRow((lastTime, row[1], row[2], row[3]))
                    else:
                        svg.addRow((lastTime, row[1], row[2],
                                    row[3], row[4], row[5]))
                svg.returnToZero()
                start = datetime.datetime.fromtimestamp(
                    firstTime).strftime('%H:%M:%S')
                end = datetime.datetime.fromtimestamp(
                    lastTime).strftime('%H:%M:%S')
                svg.diagram('/tmp/content.html', [])
                content = ''.join(svg._output)
        return content

    @staticmethod
    def secToHour(seconds):
        rc = f'{seconds // 3600:02}:{seconds % 3600 // 60:02}'
        return rc

    def yearTable(self):
        '''Builds a HTML table with the year statistics.
        '''
        sql = '''Select
  SUM(day_energy),
  SUM(day_hour8), SUM(day_hour9), SUM(day_hour10), SUM(day_hour11), SUM(day_hour12), SUM(day_hour13), 
  SUM(day_hour14), SUM(day_hour15), SUM(day_hour16), SUM(day_hour17), SUM(day_hour18), SUM(day_hourRest),
  SUM(day_energy10), SUM(day_energy25), SUM(day_energy50), SUM(day_energy100), 
  SUM(day_energy200), SUM(day_energy300), SUM(day_energy400), SUM(day_energy500), SUM(day_energy590),
  COUNT(*) 
FROM days
WHERE day_date >= %s AND day_date <= %s
;
'''
        start = datetime.datetime.strptime(
            self.fieldStart, self.i18n.formatDate).strftime('%Y-%m-%d')
        end = datetime.datetime.strptime(
            self.fieldEnd, self.i18n.formatDate).strftime('%Y-%m-%d 23:59:59')
        rows = self.dbSelect(sql, (start, end))
        row = rows[0]
        if row[1] is None:
            html = ''
        else:
            M = 13
            R = M + 9
            count = row[R + 0]
            values = {'energy': f'{row[0]/1000:.3f}', 'eavg': f'{row[0] / count / 1000:.3f}',
                      'time8': f'{row[1] / 1000:.2f}', 'time9': f'{row[2] / 1000:.2f}', 'time10': f'{row[3] / 1000:.2f}', 'time11': f'{row[4] / 1000:.2f}', 'time12': f'{row[5] / 1000:.2f}', 'time13': f'{row[6] / 1000:.2f}',
                      'time14': f'{row[7] / 1000:.2f}', 'time15': f'{row[8] / 1000:.2f}', 'time16': f'{row[9] / 1000:.2f}',
                      'time17': f'{row[10] / 1000:.2f}', 'time18': f'{row[11] / 1000:.2f}', 'time19': f'{row[12] / 1000:.2f}',
                      'tavg8': f'{row[1] / count / 1000:.3f}', 'tavg9': f'{row[2] / count / 1000:.3f}', 'tavg10': f'{row[3] / count / 1000:.3f}',
                      'tavg11': f'{row[4] / count / 1000:.3f}', 'tavg12': f'{row[5] / count / 1000:.3f}', 'tavg13': f'{row[6] / count / 1000:.3f}',
                      'tavg14': f'{row[7] / count / 1000:.3f}', 'tavg15': f'{row[8] / count / 1000:.3f}', 'tavg16': f'{row[9] / count / 1000:.3f}',
                      'tavg17': f'{row[10] / count / 1000:.3f}', 'tavg18': f'{row[11] / count / 1000:.3f}', 'tavg19': f'{row[12] / count / 1000:.3f}',
                      'min10': Service.secToHour(row[M + 0]), 'min25': Service.secToHour(row[M + 1]), 'min50': Service.secToHour(row[M + 2]),
                      'min100': Service.secToHour(row[M + 3]), 'min200': Service.secToHour(row[M + 4]), 'min300': Service.secToHour(row[M + 5]),
                      'min400': Service.secToHour(row[M + 6]), 'min500': Service.secToHour(row[M + 7]),  'min590': Service.secToHour(row[M + 8]),
                      'mavg10': Service.secToHour(row[M + 0] // count), 'mavg25': Service.secToHour(row[M + 1] // count), 'mavg50': Service.secToHour(row[M + 2] // count),
                      'mavg100': Service.secToHour(row[M + 3] // count), 'mavg200': Service.secToHour(row[M + 4] // count), 'mavg300': Service.secToHour(row[M + 5] // count),
                      'mavg400': Service.secToHour(row[M + 6] // count), 'mavg500': Service.secToHour(row[M + 7] // count),  'mavg590': Service.secToHour(row[M + 8] // count),
                      'count': f'{count}'
                      }
            i18nData = self.i18n.variables()
            html = self.snippets.asString('HTML_TABLE_YEAR', i18nData, values)
        return html

    def yearToSvg(self, start: str, end: str):
        '''Builds the SVG image from the db data.
        @param start: the start of the interval to display
        @param end: the end of the interval to display
        @returns: the SVG text
        '''
        wordsStart = start.split(' ')
        partsStart = wordsStart[0].split(self.i18n.separatorDate)
        wordsEnd = end.split(' ')
        partsEnd = wordsEnd[0].split(self.i18n.separatorDate)
        if len(partsStart) != 3 or len(partsEnd) != 3:
            content = ''
        else:
            content = ''
        return content

    def config(self):
        '''Reads the configuration file and sets the internal variables.
        '''
        if not os.path.exists(self._configFile):
            self.error(f'missing configuration {self._configFile}')
        else:
            conf = Configuration(self._configFile)
            self.interface = conf.asString('net.interface', self.interface)
            self.dayTitle = conf.asString('website.day.title')
            self.yearTitle = conf.asString('website.year.title')
            self.title = conf.asString('website.title')
            self.port = conf.asInt('net.port', self.port)
            self.i18nFilePrefix = conf.asString(
                'i18n.data', self.i18nFilePrefix)
            self.fileSnippets = conf.asString(
                'snippets.file', self.fileSnippets)
            self.bestStartDate = conf.asString('best.start.date')
            self.timeZone = conf.asInt('timezone.offset', 0)
            self.dbConfig(conf)

    def example(self):
        '''Creates an example configuration file. 
        '''
        content = f'''# Configuration for sunserver:
{SilentLog.examples()}
net.interface=localhost
net.port=8080
db.name=appsunmonitor
db.user=sun
db.code=sun4sun
website.title=My Sun Statistic
website.day.title=Sun Daily Statistic
website.year.title=Sun Year Statistic
best.start.date=2023-01-01
'''
        content += '''base=/opt/sunmonitor
i18n.data=~{base}/sunserver.i18n
i18n.languages=de en
snippets.file=~{\base\}/sunserver.snippets.html
'''
        if os.path.exists(self._configFile):
            print(f'# {self._configFile} already exists\n')
            print(content)
        else:
            with open(self._configFile, "w") as fp:
                fp.write(content)
                print("written: " + self._configFile)

    def htmlDayPage(self):
        '''Builds the HTML page of one day.
        '''
        i18nData = self.i18n.variables()
        today = datetime.datetime.now().strftime(self.i18n.formatDate)
        if self.fieldDate == '':
            self.fieldDate = today
        yesterday = (datetime.datetime.now() -
                     datetime.timedelta(days=1)).strftime(self.i18n.formatDate)
        svg = self.dayToSvg(f'{self.fieldDate} {self.fieldFrom}:00',
                            f'{self.fieldDate} {self.fieldUntil}:00')
        bestOf = self.bestOf()
        analysis = svg + '\n' + bestOf
        values = {'date': self.fieldDate,
                  'mode1': ' selected="selected"' if self.fieldMode == 1 else '',
                  'mode2': ' selected="selected"' if self.fieldMode == 2 else '',
                  'from4': ' selected="selected"' if self.fieldFrom == 4 else '',
                  'from6': ' selected="selected"' if self.fieldFrom == 6 else '',
                  'from8': ' selected="selected"' if self.fieldFrom == 8 else '',
                  'from10': ' selected="selected"' if self.fieldFrom == 10 else '',
                  'from12': ' selected="selected"' if self.fieldFrom == 12 else '',
                  'from14': ' selected="selected"' if self.fieldFrom == 14 else '',
                  'from16': ' selected="selected"' if self.fieldFrom == 16 else '',
                  'from18': ' selected="selected"' if self.fieldFrom == 18 else '',
                  'until8': ' selected="selected"' if self.fieldUntil == 8 else '',
                  'until10': ' selected="selected"' if self.fieldUntil == 10 else '',
                  'until12': ' selected="selected"' if self.fieldUntil == 12 else '',
                  'until14': ' selected="selected"' if self.fieldUntil == 14 else '',
                  'until16': ' selected="selected"' if self.fieldUntil == 16 else '',
                  'until18': ' selected="selected"' if self.fieldUntil == 18 else '',
                  'until20': ' selected="selected"' if self.fieldUntil == 20 else '',
                  'until22': ' selected="selected"' if self.fieldUntil == 22 else '',
                  'now': today, 'yesterday': yesterday, 'BODY': analysis}
        formBody = self.snippets.asString(
            'HTML_DAY_FORM_BODY', i18nData, values)

        body = self.snippets.asString('HTML_FORM', i18nData, {
                                      'action': '/day', 'method': 'POST', 'id': 'day', 'title': self.dayTitle,
                                      'FORM_BODY': formBody})
        self._content = self.snippets.asString(
            'HTML_DOCUMENT', i18nData, {'BODY': body})
        self._content = self._content.replace('~page.title~', self.title)

    def htmlYearPage(self):
        '''Builds the HTML page of the current year.
        '''
        i18nData = self.i18n.variables()
        now = datetime.datetime.now()
        if self.fieldStart == '':
            self.fieldStart = datetime.date(
                now.year, 1, 1).strftime(self.i18n.formatDate)
        if self.fieldEnd == '':
            self.fieldEnd = (now - datetime.timedelta(days=1)
                             ).strftime(self.i18n.formatDate)
        svg = self.yearToSvg(self.fieldStart, self.fieldEnd)
        analysis = svg + '\n' + self.yearTable()
        values = {'start': self.fieldStart, 'end': self.fieldEnd,
                  'BODY': analysis}
        formBody = self.snippets.asString(
            'HTML_YEAR_FORM_BODY', i18nData, values)

        body = self.snippets.asString('HTML_FORM', i18nData, {
                                      'action': '/year', 'method': 'POST', 'id': 'year', 'title': self.yearTitle,
                                      'FORM_BODY': formBody})
        self._content = self.snippets.asString(
            'HTML_DOCUMENT', i18nData, {'BODY': body})
        self._content = self._content.replace('~page.title~', self.title)
    def initService(self):
        '''Builds the file defining an SystemD service.
        '''
        with open('/etc/systemd/system/sunserver.service', 'w') as fp:
            fp.write('''[Unit]
Description=A web server displaying statistic data of a Shelly system.
After=syslog.target
[Service]
Type=simple
User=sun
Group=sun
WorkingDirectory=/opt/sunmonitor
#EnvironmentFile=-/etc/sunmonitor/sunmonitor.env
ExecStart=/opt/sunmonitor/sunmonitor.py daemon
#ExecReload=/opt/sunmonitor/sunmonitor.py reload
SyslogIdentifier=sunserver
StandardOutput=syslog
StandardError=syslog
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target

''')


class SunServer(http.server.BaseHTTPRequestHandler):
    '''Manages the HTTP server displaying statistic data of a photovoltaic device.
    '''

    def do_GET(self):
        '''Handles the GET method.
        '''
        service = Service.instance()
        if self.path.startswith('/day'):
            variables = self.path.split('?')
            if len(variables) > 1:
                date = variables[1].split('&')[0].split('=')
                if len(date) > 1 and date[0] == 'date':
                    service.fieldDate = date[1]
            self.handleDayPage(service)
        elif self.path.startswith('/year'):
            variables = self.path.split('?')
            if len(variables) > 1:
                definitions = variables[1].split('&')
                for definition in definitions:
                    pair = definition.split('=')
                    if len(pair) == 2:
                        if pair[0] == 'start':
                            self.fieldStart = pair[1]
                        elif pair[0] == 'end':
                            self.fieldEnd = pair[1]
            self.handleYearPage(service)
        else:
            service.htmlDayPage()
        self.showPage(service)

    def do_POST(self):
        '''Handles the POST method.
        '''
        service = Service.instance()
        try:
            ctype, pdict = cgi.parse_header(self.headers.get('content-type'))
            # print(f'ctype: {ctype} pdict.len: {len(pdict)}')
            pdict['boundary'] = bytes(pdict['boundary'], 'utf-8')
            if ctype == 'multipart/form-data':
                fields = cgi.parse_multipart(self.rfile, pdict)
                if self.path == '/day':
                    self.handleDayPage(service, fields)
                elif self.path == '/year':
                    self.handleYearPage(service, fields)
        except TypeError as exc:
            service.error(str(exc))
            service.htmlDayPage()
        self.showPage(service)

    def handleDayPage(self, service: Service, fields=None):
        '''Handles the form submitted from the "day" page.
        @param service: the service
        @param fields: the fields from the _POST variable
        '''
        if fields != None:
            service.fieldDate = fields.get('date')[0]
            service.fieldMode = int(fields.get('mode')[0])
            service.fieldFrom = int(fields.get('from')[0])
            service.fieldUntil = int(fields.get('until')[0])
        service.htmlDayPage()

    def handleYearPage(self, service: Service, fields=None):
        '''Handles the form submitted from the "day" page.
        @param service: the service
        @param fields: the fields from the _POST variable
        '''
        if fields != None:
            service.fieldStart = fields.get('start')[0]
            service.fieldEnd = fields.get('end')[0]
        service.htmlYearPage()

    def showPage(self, service: Service):
        '''Displays a HTML page.
        The page contents come from the service.
        @param service: the Service instance
        '''
        if service.headers != None:
            for item in service.headers:
                self.send_header(item, service.headers[item])
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        content = bytes(service._content, "utf-8")
        self.send_header("content-length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def daemon(argv):
    '''Starts a never ending HTTP server process.
    '''
    Service._instance = Service(argv)
    service = Service.instance()
    print(
        f'sunserver started: {service.interface}:{service.port} Version: {VERSION}')
    webServer = http.server.HTTPServer(
        (service.interface, service.port), SunServer)
    service.verbose = len(argv) >= 1 and argv[0] == '-v'
    if service.verbose:
        print("verbose mode")
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("Server stopped.")


def image(argv):
    service = Service.instance()
    if len(argv) < 1:
        theDate = datetime.datetime.now().strftime(service.i18n.formatDate)
    else:
        theDate = argv[0]
    parts = theDate.split('.')
    theDate = f'{parts[2]}-{parts[1]}-{parts[0]}'
    service.dayToSvg(theDate, theDate + ' 23:59:59')


def main(argv):
    mode = 'daemon' if len(argv) == 0 else argv[0]
    if mode == 'daemon':
        daemon(argv[1:])
    elif mode == 'image':
        image(argv[1:])
    elif mode == 'init-service':
        service = Service.instance()
        service.initService()
    elif mode == 'example':
        service = Service.instance()
        service.example()
    else:
        print(
            f'+++ unknown mode: {mode} Use image | init-service | example | daemon')


if __name__ == "__main__":
    main(sys.argv[1:])
