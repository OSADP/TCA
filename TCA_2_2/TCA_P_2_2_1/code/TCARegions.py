import xml.etree.ElementTree as ET
import unittest

#TCA
from TCACore import Timer, logger
from TCARandom import Random_generator

class Region(object):

    def __init__(self, title, point1, point2):

        self.title = title
        self.x1 = float(point1[0])
        self.y1 = float(point1[1])
        self.x2 = float(point2[0])
        self.y2 = float(point2[1])


    def in_region(self, x, y):
        timer.start('regions_in_region')
        if((float(x) >= self.x1) & (float(y) <= self.y1) & (float(x) <= self.x2) & (float(y) >= self.y2)):
            timer.stop()
            return True
        else:
            timer.stop()
            return False


class Cell_region(Region):

    def __init__(self, seed, title, point1, point2, loss, latency):
        Region.__init__(self, title, point1, point2)
        self.loss = loss
        self.latency = latency
        self.seed = seed

class Event_region(Region):

    def __init__(self, seed, title, point1, point2, times, events):
        Region.__init__(self, title, point1, point2)
        self.times = times
        self.events = {}


        for event in events:
            self.events[event['title']] = {'recheck' : event['recheck'],
                                     'next_check' :  times[0][0],
                                     'prev_check' : 0,
                                     'random_generator' : Random_generator(seed),
                                     'probability_type' : event['probability_type'],
            }
            if event['probability_type'] == 'probability':
                self.events[event['title']]['random_generator'].add_generator_int('rand_probability', 0, 100)
                self.events[event['title']]['probability'] =  event['probability']
            elif event['probability_type'] == 'mean':
                self.events[event['title']]['random_generator'].add_generator_mean('rand_mean', event['mean'], event['sd'])
            elif event['probability_type'] == 'poisson':
                self.events[event['title']]['random_generator'].add_generator_int('rand_probability', 0, 100)
                self.events[event['title']]['random_generator'].add_generator_poisson('recheck', event['recheck'])
                self.events[event['title']]['probability'] = event['probability']


    def in_tp(self, tp):
        timer.start('regions_in_tp')
        check = False
        for cur_tp in self.times:
            if (float(cur_tp[0]) <= float(tp) <= float(cur_tp[1])):
                check = True
                break
        timer.stop()
        return check


    def active(self, tp, x, y):
        if self.in_tp(tp):
            if self.in_region(x, y):
                return True
        return False

    def probability(self, title):
        timer.start('reigons_probability')
        if self.events[title]['probability_type'] == 'mean':
            timer.stop()
            return int(self.events[title]['random_generator']['rand_mean'])
        elif self.events[title]['probability_type'] == 'probability' or self.events[title]['probability_type'] == 'poisson':
            if int(self.events[title]['probability']) >= int(self.events[title]['random_generator']['rand_probability']):
                timer.stop()
                return 1
            else:
                timer.stop()
                return 0


    def default_value(self, title):
        timer.start('regions_default_value')
        if self.events[title]['probability_type'] == 'mean':
            timer.stop()
            return -9999
        else:
            timer.stop()
            return  0

    def check(self, title, tp, x, y):
        timer.start('regions_check')

        if tp >= self.events[title]['next_check']:
            if self.events[title]['probability_type'] != 'poisson':
                self.events[title]['next_check'] = tp + self.events[title]['recheck']
            else:
                self.events[title]['next_check'] = tp + self.events[title]['random_generator']['recheck']
            self.events[title]['prev_check'] = tp

        timer.stop('regions_check')
        timer.start('regions_active')
        if self.active(tp, x, y):
            timer.stop('regions_active')
            if self.events[title]['prev_check'] == tp:
                return self.probability(title)
            return -1234
        else:
            timer.stop('regions_active')
            return self.default_value(title)

    def check_events(self, tp, x, y):
        timer.start('regions_check_events')
        for event in self.events.keys():
            yield event, self.check(event, tp, x, y)
        timer.stop('regions_check_events')



class Regions():

    def __init__(self, seed=None):
        self.seed = seed

        #Cellular fields
        self.cell_regions = []
        self.default_latency = 0 # Default: Zero seconds
        self.default_loss = 0   # Default: 0% loss percent
        self.min_PDM_to_transmit = 4 # Default: 4 snapshots required for transmission

        #Event region fields
        self.Event_regions = []
        self.Event_titles = set()

        self.timer = Timer(enabled=True)
        global timer
        timer = self.timer

    def set_seed(self, seed):
        self.seed = seed

    def add_cell_region(self, title, point1, point2, latency, loss):
      self.cell_regions.append(
         Cell_region(
             seed = self.seed,
             title = title,
             point1 = point1,
             point2 = point2,
             latency=latency,
             loss=loss,)
        )

    def add_Event_region(self, title, point1, point2, times, events):
        self.Event_regions.append(
         Event_region(
             seed = self.seed,
             title = title,
             point1 = point1,
             point2 = point2,
             times= times,
             events = events,)
        )
def int_check(self, value, key):
    try:
        int(value)
        return int(value), ''
    except:
        return None, 'Error: %s value must be a integer' % (key)


def float_check(self, value, key):
    try:
        float(value)
        return float(value), ''
    except:
        return None, 'Error: %s value must be a float' % (key)


def Load_Regions(region_file, seed):

    #Load control_values File
    try:
        tree = ET.parse(region_file)
        root = tree.getroot()
    except:
        raise

    R = Regions(seed)

    R.default_latency = float(root.find('Cell_Regions/DefaultLatency').text)
    R.default_loss = float(root.find('Cell_Regions/DefaultLossPercent').text)
    R.min_PDM_to_transmit = int(root.find('Cell_Regions/MinPDMtoTransmit').text)

    for cell_region in root.findall('Cell_Regions/Cell_Region'):

        R.add_cell_region(
            cell_region.find('Title').text,
            (float(cell_region.find('UpperLeftPoint/X').text), float(cell_region.find('UpperLeftPoint/Y').text)),
            (float(cell_region.find('LowerRightPoint/X').text), float(cell_region.find('LowerRightPoint/Y').text)),
            float(cell_region.find('LossPercent').text),
            float(cell_region.find('Latency').text),
        )

    for region in root.findall('Event_Regions/Region'):

        region_title = region.find('Title').text
        event_point1 =  (float(region.find('UpperLeftPoint/X').text), float(region.find('UpperLeftPoint/Y').text))
        event_point2 =  (float(region.find('LowerRightPoint/X').text), float(region.find('LowerRightPoint/Y').text))

        times = []
        for time_period in region.findall('TimePeriods/Period'):
            times.append(
                (float(time_period.find('StartTime').text),
                 float(time_period.find('EndTime').text),)
            )

        events = []
        for event in region.findall('Events/Event'):

            event_title = event.find('Title').text
            R.Event_titles.add(event_title)

            if event.find('SD') != None:
                events.append(
                    {
                      'title' : event_title,
                      'recheck' : float(event.find('Recheck').text),
                      'probability_type' : 'mean',
                      'mean' :  event.find('Mean').text,
                      'sd' : event.find('SD').text ,
                    })
            elif event.find('RecheckPoisson') != None:
                events.append(
                    {
                      'title' : event_title,
                      'recheck' : float(event.find('RecheckPoisson').text),
                      'probability' : event.find('Probability').text,
                      'probability_type' : 'poisson',
                    })
            elif event.find('Probability') != None:
                events.append(
                    {
                      'title' : event_title,
                      'recheck' : float(event.find('Recheck').text),
                      'probability_type' : 'probability',
                      'probability' :  event.find('Probability').text,
                    })



        R.add_Event_region(region_title,
                           event_point1,
                           event_point2,
                           times,
                           events,)

    return R


#*************************************************************************
class RegionsTest(unittest.TestCase):

    def setUp(self):
        self.rc = Regions(12345)


    def test_region(self):
        r = Region('region1', (0,2), (2,0))
        assert r.in_region(1,1) == True
        assert r.in_region(5,5) == False


    def test_cell(self):
        self.rc.add_cell_region('region1', (0,2), (2,0), 200, 0.4)
        assert self.rc.cell_regions[0].in_region(1,1) == True
        assert self.rc.cell_regions[0].in_region(5,5) == False
        assert self.rc.cell_regions[0].latency == 200


    def test_event(self):

        times = [
            (0, 200),
            (300, 400),
        ]


        events = [
            {'title' :'temp',
             'probability_type' : 'mean',
             'recheck' : 15,
             'mean' : 30,
             'sd' : 5, },
           {'title' : 'wipers',
             'probability_type' : 'poisson',
             'recheck' : 15,
             'probability' : 20,},
           {'title' : 'traction_control',
            'probability_type' : 'probability',
            'recheck' : 1,
            'probability' :  1}
        ]

        self.rc.add_Event_region('region1', (0,2), (2,0), times, events )

        assert self.rc.Event_regions[0].check('temp', 2, 1, 1) == 25
        assert self.rc.Event_regions[0].check('temp', 3, 1, 1) == -1234
        assert self.rc.Event_regions[0].check('temp', 20, 1, 1) == 27
        assert self.rc.Event_regions[0].check('temp', 250, 1, 1) == -9999

        assert self.rc.Event_regions[0].check('wipers', 2, 1, 1) == 1
        assert self.rc.Event_regions[0].check('wipers', 20, 1, 1) == 0
        assert self.rc.Event_regions[0].check('wipers', 40, 1, 1) == 0
        assert self.rc.Event_regions[0].check('wipers', 250, 1, 1) == 0

        assert self.rc.Event_regions[0].check('traction_control', 2, 1, 1) == 0
        assert self.rc.Event_regions[0].check('traction_control', 3, 1, 1) == 0
        assert self.rc.Event_regions[0].check('traction_control', 20, 1, 1) == 0

        for event, value in self.rc.Event_regions[0].check_events(2, 1, 1):
            if event == 'traction_control':
                assert value == -1234
            elif event =='wipers':
                assert value == -1234
            elif event =='temp':
                assert value == -1234


if __name__ == '__main__':
    unittest.main()
