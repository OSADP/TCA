import xml.etree.ElementTree as ET
import unittest

#TCA
from TCACore import Timer, logger
from TCARandom import Random_generator

class Region(object):

    def __init__(self, title, point1, point2):
        """
        Base class for defining a region with a title, the upper left and bottom right point
        :param title: Title of the region
        :param point1: x,y coordinate of the upper left
        :param point2: x,y coordinate of the bottom right
        """

        self.title = title
        self.x1 = float(point1[0])
        self.y1 = float(point1[1])
        self.x2 = float(point2[0])
        self.y2 = float(point2[1])


    def in_region(self, x, y):
        """
        Determine if an x,y point falls within the region boundaries
        :param x: the x coordinate
        :param y: the y coordinate
        :return: True is the point falls within the region boundary, otherwise returns False
        """

        if((float(x) >= self.x1) & (float(y) <= self.y1) & (float(x) <= self.x2) & (float(y) >= self.y2)):
            return True
        else:
            return False


class Cell_region(Region):

    def __init__(self, title, point1, point2, loss, latency):
        """
        Defines a cellular region with a title, the upper left and bottom right point
        :param title: Title of the region
        :param point1: x,y coordinate of the upper left
        :param point2: x,y coordinate of the bottom right
        :param loss: The loss percentage of snapshots transmitted in this cellular region
        :param latency: the latency or delay time in seconds for snapshot transmission
        """
        Region.__init__(self, title, point1, point2)

        self.loss = loss
        self.latency = latency
        self.RandomGen = Random_generator()

class Event_region(Region):

    def __init__(self, title, point1, point2, times, events):
        """
        Defines an event region with a title, the upper left and bottom right point
        :param title: Title of the region
        :param point1: x,y coordinate of the upper left
        :param point2: x,y coordinate of the bottom right
        :param times: A list of times the event region is active
        :param events: A dictionary of events within the defined region
        """
        Region.__init__(self, title, point1, point2)
        self.times = times
        self.events = {}


        for event in events:
            self.events[event['title']] = {'recheck' : event['recheck'],
                                     'next_check' :  times[0][0],
                                     'prev_check' : 0,
                                     'random_generator' : Random_generator(),
                                     'probability_type' : event['probability_type'],
                                     'time_off' : event['time_off'],
                                     'next_off' : 0,
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

        """
        Determines is the current time period occurs within the event region's active time periods
        :param tp: The vehicle's current time
        :return: True if the vehicle's time occurs during the event regions active period, otherwise False
        """

        check = False
        for cur_tp in self.times:
            if (float(cur_tp[0]) <= float(tp) <= float(cur_tp[1])):
                check = True
                break
        return check


    def active(self, tp, x, y):
        """
        Determines if the event region is active for a vehicle, given the vehicle's time and coordinates
        :param tp: the vehicle's time
        :param x: the vehicle's x-coordinate
        :param y: the vehicle's y-coordinate
        :return: True if the event region is active for the vehicle, otherwise False
        """
        if self.in_tp(tp):
            if self.in_region(x, y):
                return True
        return False

    def probability(self, title):
        """
        Determines the probability of the event occuring
        :param title: The event title
        :return: 1 if the event is active, otherwise 0
        """

        if self.events[title]['probability_type'] == 'mean':
            return int(self.events[title]['random_generator']['rand_mean'])
        elif self.events[title]['probability_type'] == 'probability' or self.events[title]['probability_type'] == 'poisson':
            if int(self.events[title]['probability']) >= int(self.events[title]['random_generator']['rand_probability']):
                return 1
            else:
                return 0


    def default_value(self, title):
        """
        Determine the default value of an event in the region
        :param title: The title of the event
        :return: The default value
        """

        if self.events[title]['probability_type'] == 'mean':
            return -9999
        else:
            return  0

    def check(self, title, tp, x, y):
        """
        Determine if an event within the event region is ready for a recheck
        :param title: The event title
        :param tp: The current time period
        :param x: The vehicle's x coordinate
        :param y: The vehicle's y coordinate
        :return: A new probability, otherwise -1234 (the event region is inactive for that vehicle)
        """

        # If time for probablity recheck
        if tp >= self.events[title]['next_check']:
            if self.events[title]['probability_type'] != 'poisson':
                self.events[title]['next_check'] = tp + self.events[title]['recheck']
                self.events[title]['next_off'] = tp + self.events[title]['time_off']
            else:
                time = self.events[title]['random_generator']['recheck']
                self.events[title]['next_check'] = tp + time
                if float(self.events[title]['time_off']) != float(self.events[title]['recheck']): #If the time off value is different from the recheck value then it is user input
                    time = self.events[title]['time_off']
                self.events[title]['next_off'] = tp + time
            self.events[title]['prev_check'] = tp

        # If an active time and location for the event
        if self.active(tp, x, y):
            if (tp == self.events[title]['next_off']):
                return 0
            if self.events[title]['prev_check'] == tp:
                return self.probability(title)
            return -1234
        else:
            return self.default_value(title)

    def check_events(self, tp, x, y):
        """
        Check for any active events affecting the current vehicle
        :param tp: The vehicle's current time
        :param x: The vehicle's x-coordinate
        :param y: The vehicle's y-coordinate
        """

        for event in self.events.keys():
            yield event, self.check(event, tp, x, y)



class Regions():

    def __init__(self, seed):
        """
        This class holds all the event and cellular regions for the TCA, as well as any default values
        :param seed: A random seed for the Random Number Generators
        """

        self.RandomGen = Random_generator(seed)

        #Cellular fields
        self.cell_regions = []
        self.default_latency = 0 # Default: Zero seconds
        self.default_loss = 0   # Default: 0% loss percent
        self.min_PDM_to_transmit = 4 # Default: 4 snapshots required for transmission

        #Event region fields
        self.Event_regions = []
        self.Event_titles = set()

    def set_seed(self, seed):
        """
        Set the seed value
        :param seed: The new seed value
        """

        self.seed = seed

    def add_cell_region(self, title, point1, point2, loss, latency):
      """
      Add a cellular region to the list of cellular regions
      :param title: The cell region title
      :param point1: The x,y coordinate of the upper left point
      :param point2: The x,y coordinate of the bottom right point
      :param loss: The loss percentage rate of the cellular region
      :param latency: The latency value in seconds
      """

      self.cell_regions.append(
         Cell_region(
             title = title,
             point1 = point1,
             point2 = point2,
             loss=loss,
             latency=latency,
             )
        )

    def add_Event_region(self, title, point1, point2, times, events):
        """
        Add an event region to the list of event regions
        :param title: The event region title
        :param point1: The x,y coordinate of the upper left point
        :param point2: The x,y coordinate of the bottom right point
        :param times: A list of start and end times the event region is active
        :param events: A dictionary of active events in the region
        """

        self.Event_regions.append(
         Event_region(
             title = title,
             point1 = point1,
             point2 = point2,
             times= times,
             events = events,)
        )

    def CheckRegions(self, veh, tp):
        """
        Checks for events on a single vehicle

        :param veh: Vehicle to check
        :param tp: Time to check in
        """

        event_values = {}

        # Loop through every event in every region
        for region in self.Event_regions:
            for event, value in region.check_events(tp, veh['location_x'], veh['location_y']):

                if value == -1234: # the event region is inactive for that vehicle
                    value = veh[event]
                if event in event_values:
                    #Only replace event value if Event is True, or the vehicle event field is currently default (-9999)
                    if int(event_values[event]) == 0 or float(event_values[event]) == -9999:
                        event_values[event] = value
                else:
                    event_values[event] = value

        for event in event_values.keys():
            veh[event] = event_values[event]
        event_values.clear()


def int_check(self, value, key):
    """
    Cast a value as an integer
    :param value: The value to cast as int
    :param key: The value name
    :return: The value as an integer, otherwise an error message
    """

    try:
        int(value)
        return int(value), ''
    except:
        return None, 'Error: %s value must be a integer' % (key)


def float_check(self, value, key):
    """
    Cast a value as a float
    :param value: The value to cast as a float
    :param key: The name of the value
    :return: The value as a float, otherwise an error message
    """

    try:
        float(value)
        return float(value), ''
    except:
        return None, 'Error: %s value must be a float' % (key)


def Load_Regions(region_file, seed, unit_conversion):
    """
    Load the regions xml file
    :param region_file: File name
    :param seed: Random seed
    :param unit_conversion: unit conversion for x,y coordinates
    :return: The Regions object :raise: Errors, if any
    """

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
            (float(cell_region.find('UpperLeftPoint/X').text) * float(unit_conversion), float(cell_region.find('UpperLeftPoint/Y').text)* float(unit_conversion)),
            (float(cell_region.find('LowerRightPoint/X').text)* float(unit_conversion), float(cell_region.find('LowerRightPoint/Y').text)* float(unit_conversion)),
            float(cell_region.find('LossPercent').text),
            float(cell_region.find('Latency').text),
        )

    for region in root.findall('Event_Regions/Region'):

        region_title = region.find('Title').text
        event_point1 =  (float(region.find('UpperLeftPoint/X').text)* float(unit_conversion), float(region.find('UpperLeftPoint/Y').text)* float(unit_conversion))
        event_point2 =  (float(region.find('LowerRightPoint/X').text)* float(unit_conversion), float(region.find('LowerRightPoint/Y').text)* float(unit_conversion))

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
            if event.find('TimeOff') != None:
                time_off = float(event.find('TimeOff').text)
            elif event.find('Recheck') != None:
                time_off = float(event.find('Recheck').text)
            else:
                time_off = float(event.find('RecheckPoisson').text)


            if event.find('SD') != None:
                events.append(
                    {
                      'title' : event_title,
                      'recheck' : float(event.find('Recheck').text),
                      'probability_type' : 'mean',
                      'mean' :  event.find('Mean').text,
                      'sd' : event.find('SD').text, 
                      'time_off' : time_off,
                    })
            elif event.find('RecheckPoisson') != None:
                events.append(
                    {
                      'title' : event_title,
                      'recheck' : float(event.find('RecheckPoisson').text),
                      'probability' : event.find('Probability').text,
                      'probability_type' : 'poisson',
                      'time_off' : time_off,
                    })
            elif event.find('Probability') != None:
                events.append(
                    {
                      'title' : event_title,
                      'recheck' : float(event.find('Recheck').text),
                      'probability_type' : 'probability',
                      'probability' :  event.find('Probability').text,
                      'time_off' : time_off,
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
        self.rc.add_cell_region('region1', (0,2), (2,0), 5, 200)
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
             'sd' : 5,
             'time_off': 15 },
           {'title' : 'wipers',
             'probability_type' : 'poisson',
             'recheck' : 15,
             'probability' : 20,
             'time_off': 15},
           {'title' : 'traction_control',
            'probability_type' : 'probability',
            'recheck' : 1,
            'probability' :  1,
            'time_off' : 15}
        ]

        self.rc.add_Event_region('region1', (0,2), (2,0), times, events )


        assert self.rc.Event_regions[0].check('temp', 2, 1, 1) == 30
        assert self.rc.Event_regions[0].check('temp', 3, 1, 1) == -1234
        assert self.rc.Event_regions[0].check('temp', 20, 1, 1) == 38
        assert self.rc.Event_regions[0].check('temp', 250, 1, 1) == -9999

        assert self.rc.Event_regions[0].check('wipers', 2, 1, 1) == 0
        assert self.rc.Event_regions[0].check('wipers', 20, 1, 1) == 0
        assert self.rc.Event_regions[0].check('wipers', 40, 1, 1) == 1
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
