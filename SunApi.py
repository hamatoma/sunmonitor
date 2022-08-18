#! /usr/bin/python3
'''
Created on 27.06.2022

@author: wk
'''
import http.server
import sys
import os.path
import json
from SilentLog import SilentLog
from Configuration import Configuration

VERSION = '2022.08.18'


class Service(SilentLog):
    '''Stores and manages the data used to handle the HTTP requests.
    '''
    _instance = None

    def __init__(self, argv):
        '''Constructor.
        @param argv: the program arguments
        '''
        SilentLog.__init__(self, 100, 100)
        self._configFile = '/etc/sunmonitor/api.sun.conf'
        self._requestPath = '/rpc/Switch.GetStatus?id=0'
        self.verbose = True
        self.clientPort = 80
        self.clientIp = '192.168.2.44'
        self.serverInterface = '0.0.0.0'
        self.serverPort = 8080
        self.clientTimeout = 10
        if len(argv) > 0 and argv[0].startswith('--config='):
            self._configFile = argv[0][9:]
            argv = argv[1:]
        self.headers = None

    @staticmethod
    def instance():
        '''Returns the singleton instance of Service.
        @return: the only one instance of Service
        '''
        if Service._instance == None:
            Service._instance = Service()
        return Service._instance

    def config(self):
        '''Reads the configuration file and sets the internal variables.
        '''
        if not os.path.exists(self._configFile):
            raise Exception(f'configuration {self._configFile} does not exists')
        config = Configuration(self._configFile)
        self.silentLogConfiguration(config._variables)
        self.clientIp = config.asString('client.ip', self.clientIp)
        self.clientPort = config.asInt('client.port', self.clientPort)
        self.clientTimeout = config.asInt('client.timeout', self.clientTimeout)
        self.serverInterface = config.asString(
            'server.interface', self.serverInterface)
        self.serverPort = config.asInt('server.port', self.serverPort)

    def example(self):
        '''Creates an example configuration file. 
        '''
        content = f'''
{SilentLog.examples()}
client.ip={self.clientIp}
client.port={self.clientPort}
client.timeout={self.clientTimeout}
server.interface={self.serverInterface}
server.port={self.serverPort}
'''
        if os.path.exists(self._configFile):
            print(f'# {self._configFile} already exists\n')
            print(content)
        else:
            with open(self._configFile, "w") as fp:
                fp.write(content)
                print("written: " + self._configFile)

    def initService(self):
        '''Builds the file defining an SystemD service.
        '''
        with open('/etc/systemd/system/sunapi.service', 'w') as fp:
            fp.write('''[Unit]
Description=a proxy server for transmitting a status request of a Shelly system.
After=syslog.target
[Service]
Type=simple
User=sun
Group=sun
WorkingDirectory=/opt/sunmonitor
#EnvironmentFile=-/etc/sunmonitor/sunapi.env
ExecStart=/opt/sunmonitor/SunApi.py daemon
#ExecReload=/opt/sunmonitor/SunApi.py reload
SyslogIdentifier=sunapi
StandardOutput=syslog
StandardError=syslog
Restart=always
RestartSec=3
[Install]
WantedBy=multi-user.target

''')

    def status(self, verbose: bool=False) -> str:
        '''Handles the "status" mode of a command line request.
        @param verbose: True: print the results
        @return: the JSON data of the current status.
        '''
        rc = None
        connection = http.client.HTTPConnection(
            self.clientIp, self.clientPort, self.clientTimeout)
        try:
            connection.request("GET", self._requestPath)
            response = connection.getresponse()
            stringData = response.read()
            rc = stringData
            data = json.loads(stringData)
            if verbose:
                print('time: {}'.format(data['aenergy']['minute_ts']))
                for key in ('apower', 'voltage', 'current'):
                    print("{}: {}".format(key, data[key]))
                print('total: {}'.format(data['aenergy']['total']))
                print('temperature: {}'.format(data['temperature']['tC']))
        except:
            self.error(
                f'HTTP connection failed: {self.clientIp}:{self.clientPort}{self._requestPath}')
        connection.close()
        return rc


class SunApi(http.server.BaseHTTPRequestHandler):
    '''Manages the HTTP server to answer status requests.
    '''

    def do_GET(self):
        '''Handles the GET method.
        '''
        service = Service.instance()
        if self.path.startswith('/status'):
            self.handleStatus(service)
        else:
            prefix = self.path[0:80]
            print(f'+++ invalid request: {prefix}')
            self.showPage(service, f'What? {prefix}', 'text/plain')

    def handleStatus(self, service: Service, fields=None):
        '''Handles the POST method.
        '''
        if self.path.startswith('/status'):
            content = service.status(service)
            contentType = 'text/json'
        else:
            content = ''
            contentType = 'text/html'
        self.showPage(service, content, contentType)

    def showPage(self, service: Service, content, contentType: str):
        '''Displays a HTML page.
        The page contents come from the service.
        @param service: the Service instance
        @param content: the page content
        @param contentType: the type, e.g. "text-html"
        '''
        if service.headers != None:
            for item in service.headers:
                self.send_header(item, service.headers[item])
        self.send_response(200)
        self.send_header("Content-type", contentType)
        if type(content) == str:
            content = content.encode("utf-8")
        self.send_header("content-length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def daemon(argv):
    '''Starts a never ending HTTP server process.
    '''
    service = Service.instance()
    service.config()
    webServer = http.server.HTTPServer(
        (service.serverInterface, service.serverPort), SunApi)
    print(
        f'SunApi started: {service.serverInterface}:{service.serverPort} Version: {VERSION}')
    if len(argv) >= 1 and argv[0] == '-v':
        service.verbose = True
        argv = argv[1:]
    if len(argv) > 0:
        print(f'ignored argument(s): {" ".join(argv)}')
    if service.verbose:
        print("verbose mode")
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass
    webServer.server_close()
    print("Server stopped.")


def main(argv):
    mode = 'daemon' if len(argv) == 0 else argv[0]
    if len(argv) > 0:
        argv = argv[1:]
    Service._instance = Service(argv)
    service = Service.instance()
    if mode == 'status':
        service.config()
        service.status(True)
    elif mode == 'daemon':
        daemon(argv)
    elif mode == 'example':
        service.example()
    elif mode == 'init-service':
        service.initService()
    else:
        service.error(
            f'unknown mode: {mode} Use status | init-service | example | daemon')


if __name__ == "__main__":
    main(sys.argv[1:])
