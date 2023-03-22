#! /usr/bin/python3
'''
svgtool: Scalable Vector Graphics tool

@author: hm
'''
import os.path
import sys
import re
import datetime
import math
import functools
import StringUtils
from I18N import I18N

VERSION = '2023.03.22.00'
gSvgToolPeriod = 4


class Logger:
    def log(self, msg, level: int=0):
        print(msg)

    def error(self, msg):
        self.log('+++ ' + msg)


class SvgTool:
    '''Creates SVG data.
    '''

    def __init__(self, i18n: I18N=None):
        '''Constructor.
        @param i18n: the I18N instance
        '''
        self._columns = []
        self._rexprNo = re.compile(
            r'^\s*[+-]?\d+([.,]\d+([eE][+-]?\d+)?)?\s*$')
        self._color = 'black'
        self._strokeWidth = 2
        self._output = []
        self._fontSize = 10
        self._colors = ['black', 'red', 'orange', 'magenta', 'green', 'brown']
        self._logger = Logger()
        self.outputFileType = 'html'
        self._legendRows = None
        if i18n == None:
            i18n = I18N('de en')
            i18n.read('svgtool.i18n')
        self.tableTitle = i18n.replaceI18n('<table class="sun-table"><thead><tr><th></th><th>i18n(svg.average)</th>'
                                           + '<th>i18n(svg.minimum)</th><th>i18n(svg.maximum)</th><th>i18n(svg.conclusion)</th>'
                                           + '<th class="svg-left">i18n(svg.notice)</></tr></thead>') + '\n'

    def htmlEnd(self):
        if self.outputFileType == 'html':
            self._output.append('</body>\n</html>')

    def htmlStart(self, title):
        '''Starts a HTML script.
        '''
        if self.outputFileType == 'html':
            self._output.append('<html>\n<body>\n<h1>{}</h1>\n'.format(title))

    def simpleLine(self, x1, y1, x2, y2, strokeWidth, properties=None, color=None):
        if strokeWidth == 1:
            line = '\n<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" {}/>'.format(
                x1, y1, x2, y2, color if color != None else self._color, properties if properties != None else '')
        else:
            line = '\n<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="{}" stroke-width="{}" {}/>'.format(
                x1, y1, x2, y2, color if color != None else self._color, strokeWidth, properties if properties != None else '')
        self._output.append(line)

    def simpleText(self, x, y, text):
        self._output.append('<text x="{}" y="{}" fill="{}" font-size="{}">{}</text>'.format(
            x, y, self._color, self._fontSize, text))

    def svgEnd(self):
        self._output.append('</svg>\n')

    def svgStart(self, width, height):
        '''Starts the SVG block.
        @param width: the width of the SVG area
        @param height: the height of the SVG area
        '''
        self._output.append(
            '<svg height="{}" width="{}">\n'.format(height, width))

def usage():
    '''Returns an info about usage 
    '''
    return """svgtool [<opts>] <command>
    Builds Scalable Vector Graphics embedded in HTML.
GLOBAL_OPTS
GLOBAL_MODES
<command>:
    x-y-diagram <input-file> <output-file> <opts>
        <output-file>
            '-': output will be put to the stdout otherwise: the HTML will be put to this file
    <opt>:
        --width=<width>
            the width of the drawing area in pixel. Default: 1000
        --height=<height>
            the height of the drawing area in pixel. Default: 500
        --axis-area-width=<width>
            the width of the area containing the axis and the related labels (for x and y axis). Default: 15
        --max-average-quotient=<value>
            if max/avg(values) < maxAvgQuotient: no clipping is done. Default: 5
        --moving-average=<window-length>
            prepare data with "moving average": for each value a "window" (values and neigbours, symetic left
            and right) is used to build the average: this average is used instead of the value
            default windows width: 5
        --spread-range=<value>
            a % value: only data in this range will be displayed. Default: 90
        --spread-factor
            if abs(extremum-endOfRange) / range <= spreadFactor: the range is expanded to the extremum
                Example: data [0.5, 1, 2, 7, 99] max=7 min=1 range=7-1=6
                    abs(0.5-7)/6=1.099 1.099<1.1 => _min=0.5
                    abs(99-1)/6=16 16>1.1 => _max=99
        --title=<title>
            Default: Diagram
example:
    svgtool -v2 x-y-diagram /tmp/sinus.csv /tmp/sinus.html --width=1920 --height=1024 "--title=Trigonometric functions from [0, 4*pi]"
"""


def main(argv):
    '''The main routine.
    @param argv: the program arguments, e.g. ['/usr/local/bin/svgtool', 'run']
    '''

    if len(argv) > 2 and argv[0] == 'example':
        global gSvgToolPeriod
        try:
            gSvgToolPeriod = int(argv[1])
        except ValueError:
            pass
    tool = SvgTool()
    if len(argv) > 0 and argv[0] == 'image':
        tool.setTitles(['Zeit', 'Temperatur', 'Leistung'])
        for ix in range(100):
            tool.addRow([500 + ix, 20 + ix % 10 / 10, 300 + ix % 47 * 5])
        tool.diagram('example.html', [])
        print("example.html created")
    return 0


if __name__ == '__main__':
    main(sys.argv[1:])
