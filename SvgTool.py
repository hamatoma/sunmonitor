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

VERSION = '2022.08.02.00'
gSvgToolPeriod = 4


class Logger:
    def log(self, msg, level: int=0):
        print(msg)

    def error(self, msg):
        self.log('+++ ' + msg)


class Column:
    '''Implements a series of data, e.g. one dimension of a data collection.
    '''

    def __init__(self, title: str, parent, strokeWidth: int, displayType: str, attributes: str, comment: str):
        '''Constructor.
        @param title: the column's title
        @param parent: the array containing the column
        '''
        self._parent = parent
        self._title = title
        self._attributes = attributes
        self._strokeWidth = strokeWidth
        self._displayType = displayType
        self._comment = comment
        self._factor = 1
        if title.find('GByte') >= 0:
            self._factor = 1024 * 1024 * 1024
        elif title.find('MByte') >= 0:
            self._factor = 1024 * 1024
        elif title.find('KByte') >= 0:
            self._factor = 1024
        self._min = 1E100
        self._max = -1E100
        self._average = 0.0
        self._reducedRange = None
        self._values = []
        self._desc = False
        self._asc = False
        self._dataType = None
        self._offset = 0

    def clone(self, parent):
        rc = Column(self._title, parent, self._strokeWidth,
                    self._displayType, self._attributes, self._comment)
        return rc

    def add(self, value):
        if type(value) == str:
            value = value.strip()
        [value, dataType] = StringUtils.toFloatAndType(value)
        if dataType == 'int':
            dataType = 'float'
        if dataType == 'undef':
            raise ValueError(value)
        if self._dataType == None:
            self._dataType = dataType
        elif dataType != self._dataType:
            raise ValueError(
                'mixed data types: {} / {}'.format(dataType, self._dataType))
        self._values.append(value)

    def average(self):
        '''Returns the average of the values.
        @return: the average
        '''
        return self._average / self._factor

    def findMinMax(self, spreadRange, spreadFactor, maxAverageQuotient=40):
        '''Finds the minumum and the maximum of the data:
        spreadRange is given as % value. The extrema will be set in this way
        that only points inside this range are displayed.
        Example: data = [-5, 1, 2, 7, 99], spreadRange is 60%.
        the data inside the range are [1, 2, 7]. _max = 7, _min=1
        @param spreadRange: a % value: only data in this range will be displayed
        @param spreadFactor: @pre: greater or equal 1
                if abs(extremum-endOfRange) / range <= spreadFactor: the range is expanded to the extremum
                Example: data [0.5, 1, 2, 7, 99] max=7 min=1 range=7-1=6
                    abs(0.5-7)/6=1.099 1.099<1.1 => _min=0.5
                    abs(99-1)/6=16 16>1.1 => _max=99
        @param maxAverageQuotient: if max*min > 0 and (max / min < maxAverageQuotient: no clipping is done
        '''
        if spreadRange < 100 and len(self._values) > 0:
            # if 100 _min and _max are already set
            minValues = []
            maxItems = len(self._values) * (100.0 - spreadRange) / 100
            # round up. +1: we want the extremum outside of the excluded range:
            # plus one item
            countMax = int(maxItems + 0.5) + 1
            countMin = int(maxItems) + 1
            maxValues = []
            sum = 0.0
            countSum = 0
            ignore0 = self._attributes.find('ignore-0') >= 0
            exclude0FromAverage = self._attributes.find(
                '0-exclude-from-average') >= 0
            for val in self._values:
                if type(val) == str:
                    val = float(val)
                sum += val
                if val != 0 and not exclude0FromAverage:
                    countSum += 1
                if ignore0 and val == 0:
                    continue
                if len(minValues) < countMin:
                    minValues.append(val)
                    minValues.sort()
                elif val < minValues[-1]:
                    minValues[-1] = val
                    minValues.sort()
                if len(maxValues) < countMax:
                    maxValues.append(val)
                    maxValues.sort()
                elif val > maxValues[0]:
                    maxValues[0] = val
                    maxValues.sort()
            # get the maximum of the found values:
            self._min = minValues[-1]
            # get the minimum of the found values:
            self._max = maxValues[0]
            distance = self._max - self._min
            # we use the full range if the difference of the full range and the
            # calculated range is less than 10%:
            self._average = sum / len(self._values)
            if maxValues[-1] - self._min <= distance * spreadFactor:
                self._max = maxValues[-1]
            if self._max - minValues[0] <= distance * spreadFactor:
                self._min = minValues[0]
            if sum > 0 and self._max / self._average > maxAverageQuotient:
                self._min = minValues[0]
                self._max = maxValues[-1]

    def extremum(self, minimumNotMaximum):
        '''Returns the minimum or the maximum of the column.
        @param minimumNotMaximum: true: returns the minumum otherwise: the maximum
        @return the minimum or the maximum of the column divided by _factor
        '''
        if minimumNotMaximum:
            return self._min / self._factor
        else:
            return self._max / self._factor

    def getRange(self):
        '''Returns the difference between maximum and minimum of the column.
        @return the difference between maximum and minimum of the column divided by _factor
        '''
        return (self._max - self._min) / self._factor

    def normalize(self, offset):
        '''Scales the values to the avarage + varianz
        '''
        # column._max = functools.reduce(lambda rc, item: item if item > rc else rc, column._values, -1E+100)
        sumValues = functools.reduce(lambda rc, item: rc + item, self._values)
        standardDeviation = math.sqrt(functools.reduce(
            lambda rc, item: rc + item * item, self._values)) / len(self._values)
        average = sumValues / len(self._values)
        self._reducedRange = average + max(standardDeviation, average)
        self._offset = offset

    def getValue(self, index):
        '''Gets the index-th value of the column.
        @param index: index of _values[]
        @return the index-th value, diviced by _factor
        '''
        rc = self._values[index]
        if type(rc) != float:
            rc = StringUtils.toFloat(rc)
        return rc / self._factor

    def latest(self):
        '''Gets the last value of the column.
        @return the index-th value, diviced by _factor
        '''
        rc = self.getValue(len(self._values) - 1)
        return rc

    def toString(self, index):
        value = self.getValue(index)
        rc = StringUtils.toString(value, self._dataType)
        return rc


class AxisScale:
    '''Implements the x or y axis of a graph.
    '''

    def __init__(self, column, maxScales):
        '''Constructor.
        @param column: the column info related to the scale
        @param maxScales: maxScales / 2 < scale-count <= maxScales. scale-count is the number of markers on the scale
        '''
        self._column = column
        if column._max == -1E+100:
            column._max = functools.reduce(
                lambda rc, item: item if item > rc else rc, column._values, -1E+100)
            column._min = functools.reduce(
                lambda rc, item: item if item < rc else rc, column._values, +1E+100)
        self._scaleSize = column._reducedRange if column._reducedRange != None else column.getRange()
        rangeScale = "{:e}".format(self._scaleSize)
        if self._scaleSize == 0:
            self._countScales = 1
            self._lastScale = 0
            self._scaleStep = 1
        elif column._dataType == 'date':
            self._countScales = self._scaleSize
            self._lastScale = 0
        else:
            digit = rangeScale[1] if rangeScale[0] == '-' else rangeScale[0]
            if digit == '1' or digit == '2' or digit == '3':
                lastScale = "{:.1e}".format(column.getRange())
                digit2 = lastScale[1] if lastScale[0] == '-' else lastScale[0]
                digit3 = lastScale[3] if lastScale[0] == '-' else lastScale[2]
                self._countScales = int(digit2 + digit3)
                self._lastScale = float(lastScale)
            else:
                self._lastScale = float("{:.0e}".format(column.getRange()))
                self._countScales = int(digit)
            if self._countScales == 0:
                self._countScales = maxScales
            elif self._countScales < 0:
                self._countScales = - self._countScales
            while self._countScales * 2 <= maxScales:
                self._countScales *= 2
            while self._countScales > maxScales:
                self._countScales //= 2
            self._scaleStep = self._lastScale / self._countScales

    def indexData(self, index, length, displayType):
        '''Returns the data of a marker with a given index.
        @param index: the index of the marker (< _countScales)
        @param length: the length of the axis (width for x and height for y)
        @param displayType: None or 'time' or 'datetime'
        @return: [posMarker, label] 
        '''
        if self._countScales == 0 or self._lastScale == 0 or self._scaleSize == 0:
            posMarker = 0
            label = ''
        else:
            posMarker = int(index * length * self._lastScale /
                            self._scaleSize / self._countScales)
            value = self._column.extremum(True) + index * self._scaleStep
            dataType = self._column._dataType
            label = "{}".format(StringUtils.toString(value, dataType))
            if dataType == 'datetime' or displayType == 'datatime':
                if index == 0:
                    self._firstDate = label = datetime.datetime.fromtimestamp(
                        value).strftime('%d.%m-%H:%M')
                else:
                    label = datetime.datetime.fromtimestamp(
                        value).strftime('%d.%m-%H:%M')
            elif dataType == 'time' or displayType == 'time':
                label = datetime.datetime.fromtimestamp(
                    value).strftime('%H:%M')
            elif dataType == 'float' or dataType == 'int':
                value2 = abs(value)
                if value2 < 1:
                    label = '{:.3f}'.format(value2)
                elif value2 < 10:
                    label = '{:.2f}'.format(value2)
                elif value2 < 100:
                    label = '{:.1f}'.format(value2)
                elif value2 < 1000:
                    label = '{:.0f}'.format(value2)
                elif value2 < 10000:
                    label = '{:.1f}k'.format(value2 / 1000)
                elif value2 < 100000:
                    label = '{:.0f}k'.format(value2 / 1000)
                elif value2 < 1000000:
                    label = '{:.2f}M'.format(value2 / 1000000)
                elif value2 < 10000000:
                    label = '{:.1f}M'.format(value2 / 1000000)
                elif value2 < 10000000:
                    label = '{:.1f}M'.format(value2 / 1000000)
                else:
                    label = '{:.3g}'.format(value2)
                if value < 0:
                    label = '-' + label
        return [posMarker, label]


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

    def addLegend(self, header, average, minValue, maxValue):
        if self._legendRows == None:
            self._legendRows = [(header, average, minValue, maxValue)]
        else:
            self._legendRows.append((header, average, minValue, maxValue))

    def addRow(self, cols):
        for ix in range(len(cols)):
            self._columns[ix].add(cols[ix])

    def convertToMovingAverage(self, data, span=5):
        '''Converts an array of values inplace into an array of values with moving average.
        @param data: IN/OUT: the array of values
        @param span: the number of values which is used to calculate the average
        '''
        window = []
        sum = 0
        spanHalf = int(span / 2)
        spanHalf2 = span - spanHalf
        for ix in range(span):
            window.append(data[ix])
            sum += data[ix]
            if ix >= spanHalf:
                data[ix - spanHalf] = sum / len(window)
        for ix in range(spanHalf2, len(data) - spanHalf):
            sum -= window[0]
            window = window[1:]
            window.append(data[ix + spanHalf])
            sum += window[-1]
            data[ix] = sum / span
        for ix in range(len(data) - spanHalf, len(data)):
            sum -= window[0]
            window = window[1:]
            data[ix] = sum / len(window)

    def diagramFromFile(self, source, target, argv):
        '''Creates a SVG diagram.
        @param argv: arguments
        @return: None: OK otherwise: error message
        '''
        rc = None
        if not os.path.exists(source):
            rc = "input file {} does not exist".format(source)
        else:
            fp = None
            if target != '-':
                fp = open(target, "w")
            self.readCsv(source)
            self.diagram(target, argv)

    def diagram(self, target, argv):
        '''Creates a SVG diagram.
        @param argv: arguments
        @return: None: OK otherwise: error message
        '''
        rc = None
        if target != '-':
            fp = open(target, "w")
        width = 1000
        height = 500
        if width < len(self._columns[0]._values):
            self.shrinkData(width)
        axisAreaWidth = 15
        spreadRange = 90
        spreadFactor = 1.1
        maxAverageQuotient = 1.0
        title = 'Diagram'
        movingAverage = None
        for arg in argv:
            if arg.startswith('--width'):
                width = self.integerOption(arg)
            elif arg.startswith('--height'):
                height = self.integerOption(arg)
            elif arg.startswith('--axis-area-width'):
                axisAreaWidth = self.integerOption(arg)
            elif arg.startswith('--spread-range'):
                spreadRange = self.integerOption(arg)
                if spreadRange < 50 or spreadRange > 100:
                    self.usage('invalid value (allowed: 50..100): ' + arg)
            elif arg.startswith('--moving-average'):
                movingAverage = self.integerOption(arg, 5)
            elif arg.startswith('--spread-factor'):
                spreadFactor = self.floatArgument(arg)
            elif arg.startswith('--max-average-quotient'):
                maxAverageQuotient = self.integerOption(arg)
                if maxAverageQuotient < 1:
                    self.usage('invalid value (allowed: >= 1): ' + arg)
            elif arg.startswith('--title='):
                title = arg[8:]
            else:
                self.usage('unknown options: ' + arg)
        self._logger.log('start ' + title)
        self.htmlStart(title)
        self.svgStart(width, height)
        self.xAxis(width, height, axisAreaWidth, 0)
        for ix in range(len(self._columns) - 1):
            self._color = self._colors[ix % len(self._colors)]
            aProperty = 'stroke-dasharray="{},{}'.format(5 * (ix + 1), 3)
            for ix2 in range(ix + 1):
                aProperty += ',1,1'
            aProperty += '"'
            currentColumn = self._columns[ix + 1]
            if movingAverage != None:
                self.convertToMovingAverage(
                    currentColumn._values, movingAverage)
            currentColumn.findMinMax(
                spreadRange, spreadFactor, maxAverageQuotient)
            self.polyline(width, height, axisAreaWidth, 0, ix +
                          1, currentColumn._strokeWidth, aProperty)
            self.yAxis(width, height, axisAreaWidth, ix + 1,
                       self._color, currentColumn._strokeWidth)
        self.svgEnd()
        self.htmlLegend()
        self.htmlEnd()
        if fp == None:
            for line in self._output:
                print(line)
        else:
            for line in self._output:
                fp.write(line + '\n')
            fp.close()
        self._logger.log('end ' + title)
        return rc

    def example(self):
        '''Creates an example configuration file and example data files (sinus.csv and sinus.html). 
        '''
        example = '''# svgtool example configuration
log.file=/var/log/local/svgtool.log
width=1000
height=500
axis.area.width=15
'''
        self.storeExample(example)
        global gSvgToolPeriod
        name = '/tmp/sinus.csv'
        content = 'x;sin(x);cos(x);tan(x)\n'
        maxX = 500 - 15
        for ix in range(maxX):
            x = ix * gSvgToolPeriod * 3.141592 / maxX
            content += '{};{};{};{}\n'.format(x, math.sin(x),
                                              math.cos(x), min(1, max(-1, math.tan(x))))
        StringUtils.toFile(name, content)
        self._logger.log('created: ' + name)

    def setTitles(self, titles):
        if titles == None or len(titles) == 0:
            for ix in range(len(titles)):
                self._columns[ix]._title = "col{:d}".format(ix + 1)
        else:
            for title in titles:
                parts = title.split(';')
                title = parts[0]
                strokeWidth = 1 if len(parts) < 2 else int(parts[1])
                displayType = None if len(
                    parts) < 3 or parts[2] == '' else parts[2]
                attributes = '' if len(parts) < 4 else parts[3]
                comment = '' if len(parts) < 5 else parts[4]
                self._columns.append(
                    Column(title, self, strokeWidth, displayType, attributes, comment))

    def firstLine(self, line):
        '''Evaluates the first line.
        Searches the separator and the titles (if they exists)
        @param line: the first line to inspect
        '''
        cTab = line.count('\t')
        cComma = line.count(',')
        self._columns = []
        cSemicolon = line.count(';')
        if cTab >= cComma and cTab >= cSemicolon:
            self._separator = '\t'
        elif cSemicolon >= cComma and cSemicolon >= cTab or cSemicolon > 0 and cSemicolon == cComma - 1:
            self._separator = ';'
        else:
            self._separator = ','
        titles = line.split(self._separator)
        isNumeric = True
        for title in titles:
            self._columns.append(Column(title, self))
            if self._rexprNo.match(title) == None:
                isNumeric = False
        if isNumeric:
            self.numericLine(line, 1)
            for ix in range(len(titles)):
                self._columns[ix]._title = "col{:d}".format(ix + 1)

    def htmlEnd(self):
        if self.outputFileType == 'html':
            self._output.append('</body>\n</html>')

    def htmlLegend(self):
        '''Writes the legend of the dialog as HTML table.
        '''
        xCol = self._columns[0]
        self._output.append(
            self.tableTitle)
        dataType = xCol._displayType if xCol._displayType else xCol._dataType
        self._output.append('<tbody>\n<tr style="color: blue"><td><strong>{}:</strong></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></td><td class="svg-left">{}</td></tr>\n'
                            .format(xCol._title, '', StringUtils.toString(xCol.extremum(True), dataType, 2),
                                    StringUtils.toString(xCol.extremum(False), dataType, 2), len(xCol._values), xCol._comment))

        for ix in range(len(self._columns) - 1):
            yCol = self._columns[ix + 1]
            if yCol._attributes.find('last-is-diff') >= 0:
                lastValue = yCol.extremum(False) - yCol.extremum(True)
            else:
                lastValue = yCol.latest()
            self._output.append('<tr style="color: {}"><td><strong>{}:</strong></td><td>{:.2f}</td><td>{:.2f}</td><td>{:.2f}</td><td>{:.2f}</td><td class="svg-left">{}</td></tr>\n'
                                .format(self._colors[ix % len(self._colors)], yCol._title, yCol.average(), yCol.extremum(True),
                                        yCol.extremum(False), lastValue, yCol._comment))
        if self._legendRows != None:
            for item in self._legendRows:
                self._output.append('<tr><td>{}:</td><td>{}</td><td>{}</td><td>{}</td><td></td></tr>\n'
                                    .format(item[0], item[1], item[2], item[3]))

        self._output.append('</tbody>\n</table>\n')

    def htmlStart(self, title):
        '''Starts a HTML script.
        '''
        if self.outputFileType == 'html':
            self._output.append('<html>\n<body>\n<h1>{}</h1>\n'.format(title))

    def numericLine(self, line, lineNo):
        '''Evaluates a "numeric" line (a list of values)
        Searches the separator and the titles (if they exists)
        @param line: the line to inspect
        @param lineNo: the line number
        '''
        values = line.split(self._separator)
        if len(values) != len(self._columns):
            self._logger.error('wrong column number in line {}: {} instead of {}'.format(
                lineNo, len(values), len(self._columns)))
        for ix in range(len(values)):
            if ix < len(self._columns):
                self._columns[ix].add(StringUtils.toString(
                    values[ix], self._columns[ix]._dataType))

    def polyline(self, width, height, axisAreaWidth, indexX, indexY, strokeWidth, properties=None):
        '''Converts the CSV data into a polyline.
        @param width: the length of the x dimension
        @param height: the length of the y dimension
        @param axisAreaWidth: the width of the axis area (x and y)
        @param indexX: the column index of the x data
        @param indexy: the column index of the Y data
        @param strokeWidth: the width of the polyline
        @param properties: None or additional SVG properties for polyline, e.g. 'stroke-dasharray="5,5"
        '''
        self._output.append('\n<polyline style="fill:none;stroke:{};stroke-width:{}"{}'.format(
            self._color, self._strokeWidth, ' ' + properties if properties != None else ''))
        line = ' points="'
        xCol = self._columns[indexX]
        yCol = self._columns[indexY]
        vWidth = max(1E-10, xCol.getRange())
        vHeight = max(1E-10, yCol.getRange())
        vUsable = (height - axisAreaWidth)
        for ix in range(len(xCol._values)):
            x = axisAreaWidth + \
                int((xCol.getValue(ix) - xCol.extremum(True))
                    * (width - axisAreaWidth) / vWidth)
            yRange = yCol.extremum(False) - yCol.extremum(True)
            if yCol.getValue(ix) != None:
                # a1 = yCol.getValue(ix)
                # aE = yCol.extremum(True)
                # aR = yCol._reducedRange
                # bring y into 0..max
                y = (yCol.getValue(ix) - yCol.extremum(True))
                aY0 = y
                # normalize into 0..1:
                if yRange != 0.0:
                    y = y / yRange
                # aYnorm = y
                if yCol._reducedRange != None and yCol._reducedRange != 0:
                    y /= yCol._reducedRange
                yPixel = int(vUsable - y * vUsable)
                line += "{:g},{:g} ".format(x, yPixel)
        self._output.append(line + '" />')

    def putCsv(self, target):
        '''Puts the internal columns into a CSV file
        @param target: the full name of the result file
        '''
        with open(target, "w") as fp:
            line = ''
            for col in self._columns:
                line += col._title + ';'
            fp.write(line[0:-1] + "\n")
            for ix in range(len(self._columns[0]._values)):
                line = ''
                for col in self._columns:
                    line += col.toString(ix) + ';'
                fp.write(line[0:-1] + "\n")

    def readCsv(self, source):
        '''Reads a CSV file with the diagram data.
        @param source: the filename, e.g. 'diagram/data1.csv'
        '''
        with open(source, "r") as fp:
            lineNo = 0
            for line in fp:
                line = line.strip()
                lineNo += 1
                if lineNo == 1:
                    self.firstLine(line)
                else:
                    self.numericLine(line, lineNo)
            # Remove empty columns:
            count = len(self._columns) - 1
            for ix in range(count, -1, -1):
                column = self._columns[ix]
                if column._max == -1E+100:
                    column._max = functools.reduce(lambda rc, item: StringUtils.toFloat(
                        item) if StringUtils.toFloat(item) > rc else rc, column._values, -1E+100)
                    column._min = functools.reduce(lambda rc, item: StringUtils.toFloat(
                        item) if StringUtils.toFloat(item) < rc else rc, column._values, +1E+100)
                    # column.normalize((1 + ix % 5) / count * 0.8)
            self.returnToZero()

    def returnToZero(self):
        '''Find gaps in x values and set behind every gap a "return to zero" line
        example:
        x;y;z
        1;99;77
        2;100;70
        20;90;60
        There is a gap between line 2 and 3. Minimum gap length is 1 (between line 1 and 2)
        We insert "3;0;0" and "19;0;0"
        Result:
        x;y;z
        1;99;77
        2;100;70
        3;0;0
        19;0;0
        20;90;60
        '''
        columnX = self._columns[0]
        self._minGap = +1E+100
        [last, dummy] = StringUtils.toFloatAndType(columnX.getValue(0))
        for ix in range(len(columnX._values) - 1):
            [current, dummy] = StringUtils.toFloatAndType(
                columnX._values[1 + ix])
            if current - last < self._minGap:
                self._minGap = current - last
        if self._minGap < 5 * 60:
            self._minGap = 5 * 60
        [last, dummy] = StringUtils.toFloatAndType(columnX.getValue(-1))
        for ix in range(len(columnX._values) - 1, 1, -1):
            [current, dummy] = StringUtils.toFloatAndType(
                columnX.getValue(ix - 1))
            if last - current > self._minGap:
                columnX._values.insert(ix, last - self._minGap)
                columnX._values.insert(ix, current + self._minGap)
                for col in range(len(self._columns)):
                    if col > 0:
                        self._columns[col]._values.insert(ix, 0)
                        self._columns[col]._values.insert(ix, 0)
            last = current
        self.putCsv('/tmp/corrected.csv')

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

    def shrinkData(self, count):
        '''Returns an array of columns with count elements per column.
        Input is self._columns.
        @precondition: the first column contains the x data.
        @postcondition: the x values (first column) of the result are equidistant.
        @post: the local extrema (minimum and maximum) will be saved
        @param count: the number of items of each column of the result
        @return: the array of the converted columns
        '''
        xValues = self._columns[0]._values
        rc = []
        if count <= 0 or len(xValues) <= count:
            rc = self._columns[:]
        else:
            template = self._columns[0]
            xOut = template.clone(rc)
            rc.append(xOut)
            step = (xValues[-1] - xValues[0]) / (count - 1)
            x = xValues[0]
            # Fill the x values with count values (with equal distance>)
            for ix in range(count):
                xOut._values.append(x)
                x += step

            for ixCol in range(len(self._columns) - 1):
                yCol = self._columns[1 + ixCol]
                yValues = yCol._values
                yOut = yCol.clone(rc)
                rc.append(yOut)
                ixLastSrc = -1
                yMiddle = 0
                for ixTrg in range(count):
                    xTrg = xOut._values[ixTrg]
                    ixLastSrc += 1
                    if ixLastSrc >= len(yValues):
                        break
                    yMin = yValues[ixLastSrc]
                    if ixTrg == 0:
                        yOut._values.append(yMin)
                    elif ixTrg == count - 1:
                        yOut._values.append(yValues[-1])
                    else:
                        yMax = yMin
                        while xValues[ixLastSrc] <= xTrg:
                            if yValues[ixLastSrc] < yMin:
                                yMin = yValues[ixLastSrc]
                            elif yValues[ixLastSrc] > yMax:
                                yMax = yValues[ixLastSrc]
                            ixLastSrc += 1
                        # 4 cases: max:   min:    line up:   line down:
                        # yHigh:    a     i  i          u    d
                        #         a   a     i         u         d
                        # yLow:                     u               d
                        # xLow                                       xHigh
                        if yOut._values[ixTrg - 1] > yMax:
                            # y[ixTrg-1] is line down or max:
                            yOut._values.append(
                                yMin if ixTrg <= 1 or yValues[ixTrg - 2] > yValues[ixTrg - 1] else yMiddle)
                        else:
                            # y[ixTrg-1] is line up or min
                            yOut._values.append(
                                yMax if ixTrg <= 1 or yValues[ixTrg - 2] < yValues[ixTrg - 1] else yMiddle)
                        yMiddle = (yMax - yMin) / 2
        return rc

    def svgEnd(self):
        self._output.append('</svg>\n')

    def svgStart(self, width, height):
        '''Starts the SVG block.
        @param width: the width of the SVG area
        @param height: the height of the SVG area
        '''
        self._output.append(
            '<svg height="{}" width="{}">\n'.format(height, width))

    def xAxis(self, width, height, axisAreaWidth, indexX):
        '''Creates the x axis.
        @param width: the length of the x dimension
        @param height: the length of the y dimension
        @param axisAreaWidth: the width of the axis area (x and y)
        @param indexX: the column index of the x values
        '''
        color = self._color
        self._color = 'blue'
        self.simpleLine(axisAreaWidth, height - axisAreaWidth,
                        width, height - axisAreaWidth, self._strokeWidth)
        xCol = self._columns[indexX]
        axis = AxisScale(xCol, min((width - axisAreaWidth) / 50, 20))
        y1 = height - axisAreaWidth - self._strokeWidth * 3
        y2 = height - axisAreaWidth + self._strokeWidth * 3
        for ix in range(int(axis._countScales)):
            [pos, label] = axis.indexData(
                ix, width - axisAreaWidth, xCol._displayType)
            x = axisAreaWidth + pos
            self.simpleLine(x, y1, x, y2, self._strokeWidth)
            self.simpleText(x - 10, y2 + axisAreaWidth / 2, label)
            if ix > 0:
                self.simpleLine(x, y1 - 5, x, 0, self._strokeWidth,
                                'stroke-opacity="0.1" stroke-dasharray="5,5"', 'rgb(3,3,3)')
        self._color = color

    def yAxis(self, width, height, axisAreaWidth, indexY, color, strokeWidth):
        '''Creates the x axis.
        @param width: the length of the x dimension
        @param height: the length of the y dimension
        @param axisAreaWidth: the width of the axis area (x and y)
        @param indexY: the column index of the y values
        '''
        color2 = self._color
        self._color = color
        self.simpleLine(axisAreaWidth, 0, axisAreaWidth,
                        height - axisAreaWidth, self._strokeWidth)
        yCol = self._columns[indexY]
        axis = AxisScale(yCol, min((height - axisAreaWidth) / 50, 20))
        x1 = axisAreaWidth - self._strokeWidth * 3
        x2 = axisAreaWidth + self._strokeWidth * 3
        for ix in range(int(axis._countScales)):
            [pos, label] = axis.indexData(
                ix, height - axisAreaWidth, yCol._displayType)
            y = height - axisAreaWidth - pos
            self.simpleLine(x1, y, x2, y, self._strokeWidth)
            self.simpleText(1 + (indexY - 1) * 30, y, label)
            if indexY == 1 and ix > 0:
                self.simpleLine(x2 + 5, y, width, y, self._strokeWidth,
                                f'stroke-opacity="0.1" stroke-dasharray="5,5"', 'rgb(3,3,3)')
        self._color = color2


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
