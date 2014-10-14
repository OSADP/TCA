#standard
import math
import sys
import unittest
import time
import logging
import os

#get current directory of file
curdir = os.path.dirname(os.path.realpath(__file__)) + '\\'

def set_logger(console_level = logging.INFO, file_level = logging.DEBUG, include_file = True, append_file = False):
    """
    Creates the log file

    :param console_level: level to log items to screen
    :param file_level:  level to log items to file
    :param include_file:  include log file
    :param append_file: append to last file
    :return: logger object
    """

    if not append_file:
        try:
            os.remove(curdir + 'tca2.log')
        except:
            pass

    logger = logging.getLogger(curdir + 'tca2')
    logger.setLevel(file_level)

    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(message)s'))
    ch.setLevel(console_level)
    logger.addHandler(ch)

    if include_file:
        fh = logging.FileHandler(curdir + 'tca2.log')
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        fh.setLevel(file_level)
        logger.addHandler(fh)

    return logger


logger = set_logger(include_file = True, file_level = logging.DEBUG)

#-------------------------------------------------------------------------
def SPOT_time(tp, interval):
    """
    Determines if the timeperiod is valid for generating an ITS Spot message

    :param tp: float of current time period
    :param interval: float of the frequency for checking ITS Spot behavior record triggers
    :return: True is the tp is valid, otherwise False
    """
       
    l = [str(x) for x in range(0, 10, int(str(interval)[-1]))]
       
    if str(tp)[-1] in l:
        return True
    
    return False

#-------------------------------------------------------------------------
def Get_Heading_Change(heading_last, heading_current):
    """
    determines the change in heading

    :param heading_last: float of previous handing
    :param heading_current: float of current heading
    :return: float of the difference in heading
    """
    r = heading_current - heading_last + 180
    return (r % 360) - 180



#-------------------------------------------------------------------------
def Chk_Range(x1, y1, x2, y2):

    """
    Determine the range between two points

    :param x1: float value for X for first point
    :param y1: float value for Y for first point
    :param x2: float value for X for 2nd point
    :param y2: float value for Y for 2nd point
    :return: float distance between the two points
    """
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

    """
    determines in point is in a rectangle

    :param x1: float value for X for first point
    :param y1: float value for Y for first point
    :param x2: float value for X for 2nd point
    :param y2: float value for Y for 2nd point
    :param x3: float value for X for 3rd point
    :param y3: float value for Y for 3rd point
    :return: boolean value True if in, False if out
    """
    if((x3>=x1) & (y3<=y1) & (x3<=x2) & (y3>=y2)):
        return True
    else:
        return False

#-------------------------------------------------------------------------
def Get_Heading(x1, y1, x2, y2):
    """
    Returns the Heading based on two points

    :param x1: float value for X for first point
    :param y1: float value for Y for first point
    :param x2: float value for X for 2nd point
    :param y2: float value for Y for 2nd point
    :return: float new heading value
    """

    heading = 0
    dx = x2 - x1
    dy = y2 - y1

    if dx != 0:
      heading = (90 - math.degrees(math.atan2(dy,dx)) + 360) % 360

    elif dy > 0: heading = 0

    elif dy < 0: heading = 180

    return heading

#-------------------------------------------------------------------------
def report_errors(errors):
    """
    prints out any errors found

    :param errors: list of errors
    """
    if len(errors) > 0:
        for error in errors:
            logger.debug(error)
        sys.exit(0)


class Timer:

   def __init__(self, enabled=False):
        """
        Create Timer class

        :param enabled: Boolean if used
        """
        self.timers = {}
        self.last_start = ''
        self.enabled = enabled

   def valid_title(self, title):
       """
       Checks if title of timer item is validate

       :param title: string of title
       :return: boolean True if validate, False if not
       """
       if title in self.timers.keys() and isinstance(title, str) and self.timers[title]['count']>0:
           return True
       else:
           return False

   def __getitem__(self, title):
        """
        prints out summary information for timer

        :param title: title of time name
        :return: string of summary information about that timer
        """
        if self.valid_title(title):
                return title + ', ' + \
                       str(self.stats(title)) + ', ' + \
                       str(self.stats(title, type='max')) + ', ' + \
                       str(self.stats(title, type='avg')) + ', ' + \
                       str(self.stats(title, type='count')) + ', ' + \
                       str(self.stats(title, type='last'))
        else:
            print ('Timer Error %s not created or stopped' % title)



   def current(self, title):
       """
       Returns the current timer title

       :param title: title of timer
       :return: name of current timer or 0
       """
       if self.valid_title(title):
            return self.timers[title]['last']
       else:
            return 0


   def stats(self, title, type='SUM'):
        """
        returns the sum, max, average, count, or last value of a time title.

        :param title: name of timer value
        :param type: type of stats to produce
        :return: stat of the given timer value
        """
        if self.valid_title(title):
                if type.upper() == 'SUM':
                    return self.timers[title]['sum']
                elif type.upper() == 'MAX':
                    return self.timers[title]['max']
                elif type.upper() == 'AVG':
                    return self.timers[title]['sum'] / self.timers[title]['count']
                elif type.upper() == 'COUNT':
                    return self.timers[title]['count']
                elif type.upper() == 'LAST':
                    return  self.timers[title]['last']
        else:
            print('Error timer %s was never stopped' % title)




   def start(self, title):
       """
       starts a given timer

       :param title: string name of the timer
       """
       if self.enabled:
            if title not in self.timers.keys():
                self.timers[title] = {'st' : time.time(),
                                      'sum' : 0.0,
                                      'count' : 0,
                                      'max' : 0.0,
                                      'last' : None,
                                     }
            else:
                self.timers[title]['st'] = time.time()

            self.last_start = title


   def stop(self, title=''):
        """
        stops a given timer title

        :param title: name of the timer
        """
        if self.enabled:
            if title == '':
               title = self.last_start
            if self.timers.has_key(title):
               new_time = time.time() - self.timers[title]['st']
               self.timers[title]['sum'] +=  new_time
               self.timers[title]['count'] += 1
               self.timers[title]['last'] = new_time
               if new_time > self.timers[title]['max']:
                   self.timers[title]['max'] = new_time



   def drop(self,title):
        """
        removes timer from list

        :param title: name of a timer
        """

        if self.enabled:
            del self.timers[title]

   def header(self):
       """
       :return: string of header for timer file
       """
       return 'title,sum,max,avg,len,last\n'

   def write(self):
        """
        writes all timers values to string

        :return: string of the timer list
        """
        if self.enabled and len(self.timers) > 0:
            l = []
            for title in sorted(self.timers):
                if self.valid_title(title):
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
        assert  ( round(t1.current('test1'), 2) >= 2.0) and (t1.current('test1') < 2.1)

        t1.start('test2')
        time.sleep(3)
        t1.stop('test2')

        assert  (round(t1.current('test2'), 2) >= 3.0) and (t1.current('test2') < 3.1)

        t1.start('test2')
        time.sleep(2)
        t1.stop()
        assert  (round (t1.stats('test2'), 2) >= 5.0) and (t1.stats('test2') < 5.1)

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
        assert 0 == Get_Heading(0,-1,0,0)
        assert 45 == Get_Heading(1,1,3,3)
        assert 90 == Get_Heading(-1,0,0,0)
        assert 180 == Get_Heading(0,0,0,-1)
        assert 225 == Get_Heading(-1,-1,-5,-5)
        assert 270 == Get_Heading(0,0,-1,0)

    def test_SPOT(self):
        assert True == SPOT_time(1.3, 0.3)
        assert False == SPOT_time(1.4, 0.3)
        assert True == SPOT_time(2.0, 0.3)

if __name__ == '__main__':
    unittest.main()

