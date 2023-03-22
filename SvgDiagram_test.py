'''
Created on 18.04.2022

@author: wk
'''
import unittest
import datetime
import time
import os.path
import SvgTool as svgtool
import SvgDiagram as svgdiagram
import I18N

def fewTests():
    return True

class SvgDiagramTest(unittest.TestCase):
    def testExample(self):
        if fewTests(): return
        diagram = svgdiagram.Diagram()
        diagram.example()

    def testSinus(self):
        #if fewTests(): return
        diagram = svgdiagram.Diagram()
        diagram.example()
        target = '/tmp/sinus.html'
        argv = []
        diagram.diagramFromFile('/tmp/sinus.csv', target, argv)
        self.assertEqual(0, 0)

if __name__ == "__main__":
    unittest.main()
