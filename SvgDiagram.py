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
from enum import Enum
import SvgTool as svgtool

VERSION = '2022.08.02.00'
gSvgToolPeriod = 4

class DataType(Enum):
  undefined = 0
  string = 1
  int = 2
  float = 3
  date = 4
  datetime = 5
  time = 6

def stringToDataType(type: str) -> DataType:
    if type == 'string':
        rc = DataType.string
    elif type == 'int':
        rc = DataType.int
    elif type == 'float':
        rc = DataType.float
    elif type == 'date':
        rc = DataType.date
    elif type == 'datetime':
        rc = DataType.datetime
    elif type == 'time':
        rc = DataType.time
    else:
        rc = DataType.undefined
    return rc

class DataSet:
    '''Implements a series of data, e.g. one dimension of a data collection.
    '''

    def __init__(self, title: str, parent, strokeWidth: int=3, displayType: DataType=DataType.float, attributes: str='', comment: str=''):
        '''Constructor.
        @param title: the dataSet's title
        @param parent: the array containing the dataSet
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
        rc = DataSet(self._title, parent, self._strokeWidth,
                    self._displayType, self._attributes, self._comment)
        return rc

    def add(self, value):
        if type(value) == str:
            value = value.strip()
        [value, dataType] = toFloatAndType(value)
        if dataType == dataType.int:
            dataType = dataType.float
        if dataType == DataType.undefined:
            raise ValueError(value)
        if self._dataType == None:
            self._dataType = dataType
        elif dataType != self._dataType:
            raise ValueError(
                f'mixed data types: {dataType.name()} / {self._datatype.name()}')
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
        @param spreadFactor: @precondition: greater or equal 1
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
            startValue = 0 if len(self._values) == 0 else self._values[0]
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
        '''Returns the minimum or the maximum of the dataSet.
        @param minimumNotMaximum: true: returns the minumum otherwise: the maximum
        @return the minimum or the maximum of the dataSet divided by _factor
        '''
        if minimumNotMaximum:
            return self._min / self._factor
        else:
            return self._max / self._factor

    def getRange(self):
        '''Returns the difference between maximum and minimum of the dataSet.
        @return the difference between maximum and minimum of the dataSet divided by _factor
        '''
        return (self._max - self._min) / self._factor

    def normalize(self, offset):
        '''Scales the values to the avarage + varianz
        '''
        # dataSet._max = functools.reduce(lambda rc, item: item if item > rc else rc, dataSet._values, -1E+100)
        sumValues = functools.reduce(lambda rc, item: rc + item, self._values)
        standardDeviation = math.sqrt(functools.reduce(
            lambda rc, item: rc + item * item, self._values)) / len(self._values)
        average = sumValues / len(self._values)
        self._reducedRange = average + max(standardDeviation, average)
        self._offset = offset

    def getValue(self, index):
        '''Gets the index-th value of the dataSet.
        @param index: index of _values[]
        @return the index-th value, diviced by _factor
        '''
        rc = self._values[index]
        if type(rc) != float:
            rc = StringUtils.toFloat(rc)
        return rc / self._factor

    def latest(self):
        '''Gets the last value of the dataSet.
        @return the index-th value, diviced by _factor
        '''
        rc = self.getValue(len(self._values) - 1)
        return rc

    def toString(self, index):
        value = self.getValue(index)
        rc = toString(value, self._dataType)
        return rc


class AxisScale:
    '''Implements the x or y axis of a graph.
    '''
    def __init__(self, dataSet, maxScales):
        '''Constructor.
        @param dataSet: the dataSet info related to the scale
        @param maxScales: maxScales / 2 < scale-count <= maxScales. scale-count is the number of markers on the scale
        '''
        self._dataSet = dataSet
        if dataSet._max == -1E+100:
            dataSet._max = max(dataSet._values)
            dataSet._min = min(dataSet._values)
        self._startValueScale, self._stepScale, self._countScales = self.buildScaleData(dataSet._min, dataSet._max, dataSet._displayType, maxScales)
        self._scaleSize = dataSet._reducedRange if dataSet._reducedRange != None else dataSet.getRange()

    def buildScaleData(self, minValue, maxValue, dataType: DataType, maxScales: int):
        '''Returns a tuple (startValue, step, count) for building marker lines of a diagram.
        The start value and the other marker values (startValue + N * step) should be "round" values.
        
        @param minValue the minimum of the values
        @param maxValue the maximum of the values
        @param dataType: the type of the value
        @param maxScales: the maximum marker lines
        @return: (startValue, step, count)
        '''
        range = maxValue - minValue
        step = float(f'{range / maxScales:.0g}')
        if dataType == DataType.int:
            step = int(range * 10) // 10
        elif dataType == DataType.float:
            pass
        elif dataType == DataType.datetime or dataType == DataType.date:
            # range in days
            if range > 10:
                step = int(range * 10) // 10
            elif range > 5:
                step = 0.5
            elif range > 1:
                step = 1/12
            else:
                step = 1/24
        elif dataType == DataType.time:
            step = 2.0 if range > 20 else (1.0 if range > 10 else 0.5)
        if step == 0.0:
            step = 1
        start = math.floor(minValue * step) / step
        while step * 2 < (maxValue - start) / maxScales:
            step *= 2
        count = int((range + step*0.9)/ step)
        return (start, step, count)

    def scaleDataByIndex(self, index, length, displayType):
        '''Returns the data of a marker with a given index.
        @param index: the index of the marker (< _countScales)
        @param length: the length of the axis (width for x and height for y)
        @param displayType: None or 'time' or 'datetime'
        @return: (posMarker, label)
        '''
        if self._countScales == 0 or self._scaleSize == 0:
            posMarker = 0
            label = ''
        else:
            relative = self._dataSet._attributes.find('relative-to-start') >= 0
            posMarker = int(index * length / self._countScales)
            value = self._startValueScale + index * self._stepScale
            dataType = self._dataSet._dataType
            label = "{}".format(toString(value, dataType))
            if dataType == DataType.datetime or displayType == DataType.datetime:
                if index == 0:
                    self._firstDate = label = datetime.datetime.fromtimestamp(
                        value).strftime('%d.%m-%H:%M')
                else:
                    label = datetime.datetime.fromtimestamp(
                        value).strftime('%d.%m-%H:%M')
            elif dataType == DataType.time:
                label = datetime.datetime.fromtimestamp(
                    value).strftime('%H:%M')
            elif displayType == DataType.time:
                label = f'{math.floor(value)}:{math.floor(value*60+0.5)%60:02d}'
            elif dataType == DataType.float or dataType == DataType.int:
                if relative:
                    value2 = abs(value - self._dataSet._values[0])
                else:
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
        return (posMarker, label)

class Diagram(svgtool.SvgTool):
    def __init__(self, i18n: I18N=None):
        svgtool.SvgTool.__init__(self, i18n)
        self._dataSets = []
        self._legendRows = None

    def addLegend(self, header, average, minValue, maxValue):
        if self._legendRows == None:
            self._legendRows = [(header, average, minValue, maxValue)]
        else:
            self._legendRows.append((header, average, minValue, maxValue))


    def addRow(self, cols):
        for ix in range(len(cols)):
            self._dataSets[ix].add(cols[ix])

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

    def csvPolyline(self, width, height, axisAreaWidth, indexX, indexY, strokeWidth, properties=None):
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
        xDataSet = self._dataSets[indexX]
        yDataSet = self._dataSets[indexY]
        vWidth = max(1E-10, xDataSet.getRange())
        vHeight = max(1E-10, yDataSet.getRange())
        vUsable = (height - axisAreaWidth)
        for ix in range(len(xDataSet._values)):
            x = axisAreaWidth + \
                int((xDataSet.getValue(ix) - xDataSet.extremum(True))
                    * (width - axisAreaWidth) / vWidth)
            yRange = yDataSet.extremum(False) - yDataSet.extremum(True)
            if yDataSet.getValue(ix) != None:
                # a1 = yDataSet.getValue(ix)
                # aE = yDataSet.extremum(True)
                # aR = yDataSet._reducedRange
                # bring y into 0..max
                y = (yDataSet.getValue(ix) - yDataSet.extremum(True))
                aY0 = y
                # normalize into 0..1:
                if yRange != 0.0:
                    y = y / yRange
                # aYnorm = y
                if yDataSet._reducedRange != None and yDataSet._reducedRange != 0:
                    y /= yDataSet._reducedRange
                yPixel = int(vUsable - y * vUsable)
                line += "{:g},{:g} ".format(x, yPixel)
        self._output.append(line + '" />')

    def diagramFromFile(self, source, target, argv):
        '''Creates a SVG diagram.
        @param argv: arguments
        @return: None: OK otherwise: error message
        '''
        rc = None
        if not os.path.exists(source):
            rc = f'input file {source} does not exist'
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
        if width < len(self._dataSets[0]._values):
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
        for ix in range(len(self._dataSets) - 1):
            self._color = self._colors[ix % len(self._colors)]
            aProperty = 'stroke-dasharray="{},{}'.format(5 * (ix + 1), 3)
            for ix2 in range(ix + 1):
                aProperty += ',1,1'
            aProperty += '"'
            currentDataSet = self._dataSets[ix + 1]
            if movingAverage != None:
                self.convertToMovingAverage(
                    currentDataSet._values, movingAverage)
            currentDataSet.findMinMax(
                spreadRange, spreadFactor, maxAverageQuotient)
            self.csvPolyline(width, height, axisAreaWidth, 0, ix +
                          1, currentDataSet._strokeWidth, aProperty)
            self.yAxis(width, height, axisAreaWidth, ix + 1,
                       self._color, currentDataSet._strokeWidth)
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

    def firstLine(self, line):
        '''Evaluates the first line.
        Searches the separator and the titles (if they exists)
        @param line: the first line to inspect
        '''
        cTab = line.count('\t')
        cComma = line.count(',')
        self._dataSets = []
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
            self._dataSets.append(DataSet(title, self))
            if self._rexprNo.match(title) == None:
                isNumeric = False
        if isNumeric:
            self.numericLine(line, 1)
            for ix in range(len(titles)):
                self._dataSets[ix]._title = "col{:d}".format(ix + 1)

    def htmlLegend(self):
        '''Writes the legend of the dialog as HTML table.
        '''
        xDataSet = self._dataSets[0]
        self._output.append(
            self.tableTitle)
        dataType = xDataSet._displayType if xDataSet._displayType else xDataSet._dataType
        self._output.append('<tbody>\n<tr style="color: blue"><td><strong>{}:</strong></td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></td><td class="svg-left">{}</td></tr>\n'
                            .format(xDataSet._title, '', StringUtils.toString(xDataSet.extremum(True), dataType, 2),
                                    StringUtils.toString(xDataSet.extremum(False), dataType, 2), len(xDataSet._values), xDataSet._comment))

        for ix in range(len(self._dataSets) - 1):
            yDataSet = self._dataSets[ix + 1]
            if yDataSet._attributes.find('last-is-diff') >= 0:
                lastValue = yDataSet.extremum(False) - yDataSet.extremum(True)
            else:
                lastValue = yDataSet.latest()
            self._output.append('<tr style="color: {}"><td><strong>{}:</strong></td><td>{:.2f}</td><td>{:.2f}</td><td>{:.2f}</td><td>{:.2f}</td><td class="svg-left">{}</td></tr>\n'
                                .format(self._colors[ix % len(self._colors)], yDataSet._title, yDataSet.average(), yDataSet.extremum(True),
                                        yDataSet.extremum(False), lastValue, yDataSet._comment))
        if self._legendRows != None:
            for item in self._legendRows:
                self._output.append('<tr><td>{}:</td><td>{}</td><td>{}</td><td>{}</td><td></td></tr>\n'
                                    .format(item[0], item[1], item[2], item[3]))

        self._output.append('</tbody>\n</table>\n')

    def putCsv(self, target):
        '''Puts the internal columns into a CSV file
        @param target: the full name of the result file
        '''
        with open(target, "w") as fp:
            line = ''
            for col in self._dataSets:
                line += col._title + ';'
            fp.write(line[0:-1] + "\n")
            for ix in range(len(self._dataSets[0]._values)):
                line = ''
                for col in self._dataSets:
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
            count = len(self._dataSets) - 1
            for ix in range(count, -1, -1):
                dataSet = self._dataSets[ix]
                if dataSet._max == -1E+100:
                    dataSet._max = functools.reduce(lambda rc, item: StringUtils.toFloat(
                        item) if StringUtils.toFloat(item) > rc else rc, dataSet._values, -1E+100)
                    dataSet._min = functools.reduce(lambda rc, item: StringUtils.toFloat(
                        item) if StringUtils.toFloat(item) < rc else rc, dataSet._values, +1E+100)
                    # dataSet.normalize((1 + ix % 5) / count * 0.8)
            self.returnToZero()

    def numericLine(self, line, lineNo):
        '''Evaluates a "numeric" line (a list of values)
        @param line: the line to inspect
        @param lineNo: the line number
        '''
        values = line.split(self._separator)
        if len(values) != len(self._dataSets):
            self._logger.error('wrong column number in line {}: {} instead of {}'.format(
                lineNo, len(values), len(self._dataSets)))
        for ix in range(len(values)):
            if ix < len(self._dataSets):
                self._dataSets[ix].add(toString(
                    values[ix], self._dataSets[ix]._dataType))

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
        dataSetX = self._dataSets[0]
        self._minGap = +1E+100
        [last, dummy] = toFloatAndType(dataSetX.getValue(0))
        for ix in range(len(dataSetX._values) - 1):
            [current, dummy] = toFloatAndType(
                dataSetX._values[1 + ix])
            if current - last < self._minGap:
                self._minGap = current - last
        if self._minGap < 5 * 60:
            self._minGap = 5 * 60
        [last, dummy] = toFloatAndType(dataSetX.getValue(-1))
        for ix in range(len(dataSetX._values) - 1, 1, -1):
            [current, dummy] = toFloatAndType(
                dataSetX.getValue(ix - 1))
            if last - current > self._minGap:
                dataSetX._values.insert(ix, last - self._minGap)
                dataSetX._values.insert(ix, current + self._minGap)
                for col in range(len(self._dataSets)):
                    if col > 0:
                        self._dataSets[col]._values.insert(ix, 0)
                        self._dataSets[col]._values.insert(ix, 0)
            last = current
        self.putCsv('/tmp/corrected.csv')

    def xAxis(self, width, height, axisAreaWidth, indexX):
        '''Creates the x axis.
        @param width: the length of the x dimension
        @param height: the length of the y dimension
        @param axisAreaWidth: the width of the axis area (x and y)
        @param indexX: the dataSet index of the x values
        '''
        color = self._color
        self._color = 'blue'
        self.simpleLine(axisAreaWidth, height - axisAreaWidth,
                        width, height - axisAreaWidth, self._strokeWidth)
        xDataSet = self._dataSets[indexX]
        axis = AxisScale(xDataSet, 20)
        y1 = height - axisAreaWidth - self._strokeWidth * 3
        y2 = height - axisAreaWidth + self._strokeWidth * 3
        for ix in range(int(axis._countScales)):
            [pos, label] = axis.scaleDataByIndex(
                ix, width - axisAreaWidth, xDataSet._displayType)
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
        @param indexY: the dataSet index of the y values
        '''
        color2 = self._color
        self._color = color
        self.simpleLine(axisAreaWidth, 0, axisAreaWidth,
                        height - axisAreaWidth, self._strokeWidth)
        yDataSet = self._dataSets[indexY]
        axis = AxisScale(yDataSet, 10)
        x1 = axisAreaWidth - self._strokeWidth * 3
        x2 = axisAreaWidth + self._strokeWidth * 3
        for ix in range(int(axis._countScales)):
            [pos, label] = axis.scaleDataByIndex(
                ix, height - axisAreaWidth, yDataSet._displayType)
            y = height - axisAreaWidth - pos
            self.simpleLine(x1, y, x2, y, self._strokeWidth)
            self.simpleText(1 + (indexY - 1) * 30, y, label)
            if indexY == 1 and ix > 0:
                self.simpleLine(x2 + 5, y, width, y, self._strokeWidth,
                                f'stroke-opacity="0.1" stroke-dasharray="5,5"', 'rgb(3,3,3)')
        self._color = color2
    def example(self):
        '''Creates an example configuration file and example data files (sinus.csv and sinus.html). 
        '''
        example = '''# svgtool example configuration
log.file=/var/log/local/svgtool.log
width=1000
height=500
axis.area.width=15
'''
        filename = '/etc/sunmonitor/svgtool.example'
        StringUtils.toFile(filename, example)
        print(f'written: {filename}')
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
                self._dataSets[ix]._title = "col{:d}".format(ix + 1)
        else:
            for title in titles:
                parts = title.split(';')
                title = parts[0]
                strokeWidth = 1 if len(parts) < 2 else int(parts[1])
                displayType = None if len(
                    parts) < 3 or parts[2] == '' else parts[2]
                attributes = '' if len(parts) < 4 else parts[3]
                comment = '' if len(parts) < 5 else parts[4]
                displayTime2 = stringToDataType(displayType)
                if displayTime2 == DataType.undefined:
                    displayTime2 = DataType.float
                self._dataSets.append(
                    DataSet(title, self, strokeWidth, displayTime2, attributes, comment))

    def shrinkData(self, count):
        '''Returns an array of columns with count elements per column.
        Input is self._dataSets.
        @precondition: the first column contains the x data.
        @postcondition: the x values (first column) of the result are equidistant.
        @post: the local extrema (minimum and maximum) will be saved
        @param count: the number of items of each column of the result
        @return: the array of the converted columns
        '''
        xValues = self._dataSets[0]._values
        rc = []
        if count <= 0 or len(xValues) <= count:
            rc = self._dataSets[:]
        else:
            template = self._dataSets[0]
            xOut = template.clone(rc)
            rc.append(xOut)
            step = (xValues[-1] - xValues[0]) / (count - 1)
            x = xValues[0]
            # Fill the x values with count values (with equal distance>)
            for ix in range(count):
                xOut._values.append(x)
                x += step

            for ixCol in range(len(self._dataSets) - 1):
                yCol = self._dataSets[1 + ixCol]
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

def usage():
    '''Returns an info about usage 
    '''
    return """svgdiagram [<opts>] <command>
    Builds Scalable Vector Graphics embedded in HTML.
<command>:
    draw <input-file> <output-file> <opts>
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
    svgtool -v2 draw /tmp/sinus.csv /tmp/sinus.html --width=1920 --height=1024 "--title=Trigonometric functions from [0, 4*pi]"
"""

def toFloatAndType(value):
    '''Converts a string into a float.
    Possible data types: int, date, datetime, float.
    Value of date/datetime: days since 1.1.1970 (float value)
    Value of time: hours since midnight: 0.0..24.0
    @param value: the string to convert
    @return [float, dataType] or [error_message, dataType] 
    '''
    dataType = DataType.undefined
    if type(value) == float:
        dataType = DataType.float
        rc = value
    elif type(value) == int:
        dataType = dataType.float
        rc = float(value)
    else:
        matcher = StringUtils.stringUtilRexprDate.match(value)
        if matcher != None:
            dataType = DataType.date
            length = len(matcher.group(0))
            value = value[length + 1:]
            rc = datetime.datetime(int(matcher.group(1)), int(
                matcher.group(2)), int(matcher.group(3))).timestamp() / SEC_PER_DAY
            matcher = stringUtilRexprTime.match(value)
            if matcher != None:
                dataType = DataType.datetime
                hours, mins = int(matcher.group(1)), int(matcher.group(2))
                secs = (hours * 60 + mins) * 60
                rc += secs / SEC_PER_DAY
                if matcher.group(3):
                    rc += int(matcher.group(3)) / SEC_PER_DAY
        else:
            matcher = StringUtils.stringUtilRexprTime.match(value)
            if matcher != None:
                hours, mins = int(matcher.group(1)), int(matcher.group(2))
                dataType = DataType.time
                rc = (hours * 60 + mins) * 60 / 3600.0
                if matcher.group(3):
                    rc += int(matcher.group(3)) / 3600.0
            else:
                matcher = StringUtils.stringUtilRexprInt.match(value)
                if matcher != None:
                    dataType = DataType.int
                    if matcher.group(3):
                        rc = float(matcher.group(3))
                    elif matcher.group(1):
                        rc = float(int(value[2:], 16))
                    elif matcher.group(2):
                        rc = float(int(value, 8))
                else:
                    try:
                        rc = float(value)
                        dataType = DataType.float
                    except ValueError:
                        rc = 'float (or int or date(time)) expected, found: ' + value
    return [rc, dataType]


def toString(value, dataType, floatPrecision=None):
    '''Converts a numeric value into a string.
    @param value: a numeric value
    @param dataType: 'date', 'datetime', 'time', 'float', 'int'
    @param floatPrecision: None or if the type is a float, the number of digits behind the point
    @return: the value as string
    '''
    SEC_PER_DAY = 86400.0
    if type(value) == str:
        rc = value
    else:
        if dataType == None:
            if type(value) == int:
                dataType = DataType.int
            elif type(value) == float:
                dataType = DataType.float
            elif type(value) == datetime.datetime:
                dataType = DataType.datetime
            elif type(value) == datetime.date:
                dataType = DataType.date
        if dataType == DataType.date:
            date = datetime.datetime.fromtimestamp(int(value*SEC_PER_DAY))
            rc = date.strftime('%Y.%m.%d')
        elif dataType == DataType.datetime:
            if type(value) == str and value.find(':') >= 0:
                rc = value
            else:
                date = datetime.datetime.fromtimestamp(int(value*SEC_PER_DAY))
                rc = date.strftime('%Y.%m.%d %H:%M')
        elif dataType == DataType.time:
            if type(value) == DataType.string and value.find(':') >= 0:
                rc = value
            else:
                if value > SEC_PER_DAY:
                    rc = datetime.datetime.fromtimestamp(value).strftime('%H:%M')
                else:
                    rc = '{:2d}:{:2d}'.format(value / 3600, value % 3600 / 60)
        elif floatPrecision != None:
            if type(value) == str:
                value = float(value)
            aFormat = '{' + ':.{}f'.format(floatPrecision) + '}'
            rc = aFormat.format(value)
        else:
            rc = f'{value}'
    return rc


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
