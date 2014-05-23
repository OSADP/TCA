#standard
import math
import sys
import unittest
import time

#---------------------------------------------------------------------------
#Strategy Global Variables



class ControlVars:
    Strategy = dict()
    Control = dict()
    Debugger = None
    RandomGen = None

#Strategy Definition Variables
def init():
    global Strategy
    global Control
    global Debugger
    global RandomGen

    Strategy = dict()
    Control = dict()
    Debugger = None
    RandomGen = None

def Chk_Range(x1, y1, x2, y2):

    unitValue = 1 #1 = linear distance #2 - Spherical distance

    ran = None

    if unitValue ==1:
        ran = math.sqrt((float(y2) - float(y1)) ** 2 + (float(x2) - float(x1)) ** 2)
    elif unitValue==2:

        rad = 3958.76 #Earth radius in Miles

        #Convert to radians
        p1lat = float(x1) / 180 * math.pi
        p1long = float(y1) / 180 * math.pi
        p2lat = float(x2) / 180 * math.pi
        p2long = float(y2) / 180 * math.pi

        if (p1lat == p2lat) and (p1long == p2long):
            ran = float(0)
        else:
            ran = math.acos(math.sin(p1lat) * math.sin(p2lat) + math.cos(p1lat) * math.cos(p2lat)
                  * math.cos(p2long - p1long)) * rad

    return ran

# (x1,y1) : Top left of rectangle, (x2,y2) : Bottom right of rectangle, (x3,y3) : Point in question
def Chk_Cellular_Range(x1, y1, x2, y2, x3, y3):

    if((x3>=x1) & (y3<=y1) & (x3<=x2) & (y3>=y2)):
        return True
    else:
        return False

def Get_Heading(lat1, long1, lat2, long2):
    heading = 0
    y = math.sin(long2-long1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(long2-long1)
    heading = (math.degrees(math.atan2(y,x)) + 360) % 360
    return heading

def report_errors(errors):
    if len(errors) > 0:
        for error in errors:
            print error
        sys.exit(0)

class Timer:

    def __init__(self):
        self.timers = {}
        self.last_start = ''


    def start(self, title):
        if title not in self.timers.keys():
            self.timers[title] = {'total' : 0,
                                  'st' : time.time(),
                                  'et' : 0}
        else:
            self.timers[title]['st'] = time.time()
            self.timers[title]['et'] = 0
        self.last_start = title



    def stop(self, title=''):
        if title == '':
            title = self.last_start
        if self.timers.has_key(title):
            self.timers[title]['et'] = time.time()
            self.timers[title]['total'] += self.timers[title]['et'] - self.timers[title]['st']

    def drop(self,title):
        del self.timers[title]

    def write(self):
        l = []
        for title in self.timers:
            l.append("%s,%s" % (title,  self.timers[title]['total']))
        return '\n'.join(l)

    def __str__(self):
        s = ''
        for title in self.timers:
                s += "%s,%s\n" % (title,  self.timers[title]['total'])
        return s[:-2]




class TestTimer(unittest.TestCase):

    def test_timer(self):
        t1=Timer()

        t1.start('test1')
        time.sleep(2)
        t1.stop()
        assert  (t1.timers['test1']['total'] >= 2.0) and (t1.timers['test1']['total'] < 2.1)

        t1.start('test2')
        time.sleep(3)
        t1.stop('test2')

        assert  (t1.timers['test2']['total'] >= 3.0) and (t1.timers['test2']['total'] < 3.1)

        t1.start('test2')
        time.sleep(2)
        t1.stop()
        assert  (t1.timers['test2']['total'] >= 5.0) and (t1.timers['test2']['total'] < 5.1)

class CoreTests(unittest.TestCase):

    def test_range(self):
        assert 1 == int(Chk_Range(1,1,2,2))
        assert 5.0 == Chk_Range(-2,1,1,5)
        assert 0.0 == Chk_Range(1,1,1,1)

    def test_errors(self):
        e = []
        report_errors(e)

    def test_cellular_range(self):
        assert True == Chk_Cellular_Range(-2,1,0,0,-1,1)
        assert False == Chk_Cellular_Range(-2,1,0,0,1,0)

    def test_heading(self):
        heading = int(Get_Heading(42.5,-36.2,42.5,-36.3))
        assert 267 == heading




if __name__ == '__main__':
    unittest.main()