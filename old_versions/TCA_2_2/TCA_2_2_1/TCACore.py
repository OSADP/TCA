#standard
import math
import sys
import unittest
import time
import logging
import os


def set_logger(console_level = logging.INFO, file_level = logging.DEBUG, include_file = True, append_file = False):

    if not append_file:
        try:
            os.remove('tca2.log')
        except:
            pass

    logger = logging.getLogger('tca2')
    logger.setLevel(file_level)

    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(message)s'))
    ch.setLevel(console_level)
    logger.addHandler(ch)

    if include_file:
        fh = logging.FileHandler('tca2.log')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        fh.setLevel(file_level)
        logger.addHandler(fh)

    return logger


logger = set_logger(include_file = True, file_level = logging.DEBUG)


#-------------------------------------------------------------------------
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

#-------------------------------------------------------------------------
# (x1,y1) : Top left of rectangle, (x2,y2) : Bottom right of rectangle, (x3,y3) : Point in question
def Chk_Cellular_Range(x1, y1, x2, y2, x3, y3):

    if((x3>=x1) & (y3<=y1) & (x3<=x2) & (y3>=y2)):
        return True
    else:
        return False

#-------------------------------------------------------------------------
def Get_Heading(lat1, long1, lat2, long2):
    heading = 0
    y = math.sin(long2-long1) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(long2-long1)
    heading = (math.degrees(math.atan2(y,x)) + 360) % 360
    return heading

#-------------------------------------------------------------------------
def report_errors(errors):
    if len(errors) > 0:
        for error in errors:
            print error
        sys.exit(0)




class Timer:

   def __init__(self, enabled=False):
        self.timers = {}
        self.last_start = ''
        self.enabled = enabled

   def valid_title(self, title):
       if title in self.timers.keys() and isinstance(title, str):
           return True
       else:
           return False

   def __getitem__(self, title):
        if self.valid_title(title) :
            # print title
            return title + ',' + \
                   str(self.stats(title)) + ',' + \
                   str(self.stats(title, type='max')) + ',' + \
                   str(self.stats(title, type='avg')) + ',' + \
                   str(len(self.timers[title]['values'])) + ',' + \
                   str(self.timers[title]['values'][-1])

   def current(self, title):
       if self.valid_title(title):
            return self.timers[title]['values'][-1]
       else:
           return 0



   def stats(self, title, type='SUM'):
        if self.valid_title(title):
            if len(self.timers[title]['values']) > 0:
                if type.upper() == 'SUM':
                    return sum(self.timers[title]['values'])
                elif type.upper() == 'MAX':
                    return max(self.timers[title]['values'])
                elif type.upper() == 'AVG':
                    return sum(self.timers[title]['values']) / len(self.timers[title]['values'])



   def start(self, title):
       if self.enabled:
            if title not in self.timers.keys():
                self.timers[title] = {'st' : time.time(),
                                      'values': []}
            else:
                self.timers[title]['st'] = time.time()

            self.last_start = title



   def stop(self, title=''):
        if self.enabled:
            if title == '':
                title = self.last_start
            if self.timers.has_key(title):
                end_time = time.time()
                self.timers[title]['values'].append(end_time - self.timers[title]['st'])

   def drop(self,title):
        if self.enabled:
            del self.timers[title]

   def header(self):
       return 'title,sum,max,avg,len,last\n'

   def write(self):
        if self.enabled:
            l = []
            for title in self.timers:
                l.append(self.__getitem__(title))
            return '\n'.join(l)
        else:
            return ''




#*************************************************************************
class TestTimer(unittest.TestCase):

    def test_timer(self):
        t1=Timer(enabled = True)

        t1.start('test1')
        time.sleep(2)
        t1.stop()
        assert  (t1.current('test1') >= 2.0) and (t1.current('test1') < 2.1)

        t1.start('test2')
        time.sleep(3)
        t1.stop('test2')

        assert  (t1.current('test2') >= 3.0) and (t1.current('test2') < 3.1)

        t1.start('test2')
        time.sleep(2)
        t1.stop()
        assert  (t1.stats('test2') >= 5.0) and (t1.stats('test2') < 5.1)

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
        assert 0 == Get_Heading(-1,0,0,0)
        assert 90 == Get_Heading(0,-1,0,0)
        assert 180 == Get_Heading(0,0,-1,0)
        assert 270 == Get_Heading(0,0,0,-1)

if __name__ == '__main__':
    unittest.main()

