import xml.etree.ElementTree as ET
import unittest
import string
import re
import sys
import os
from math import floor
#TCA
from TCACore import Timer, logger
from TCARandom import Random_generator
from TCARegions import Load_Regions

class Trigger(object):
    def __init__(self, title, start_trigger, end_trigger, BMM_Type, random_generator, gen_params = {}, target_params = {}, queue_params = {}, burst_params = {}, turn_params = {}, link_lengths = None, routes = None):
        """Base class for defining a trigger with at least a title and the start and end expressions
        :param title: Trigger title
        :param start_trigger: Expression to turn on trigger
        :param end_trigger: Expression to turn off trigger
        :param BMM_Type: the BMM type associated with the trigger
        :param gen_params: general parameters
        :param target_params: target parameters
        :param queue_params: queue parameters
        :param burst_params: burst parameters
        :param turning_params: turning parameters 
        """

        self.title = title
        self.start_trigger = start_trigger
        self.end_trigger = end_trigger
        self.BMM_Type = BMM_Type
        
        #GenerationMeanTime a dictionary who's keys are the specific regions, and value are the generation mean time. General case is -1. 
        self.GenerationMeanTime = {-1: gen_params.get('GenerationMeanTime',50)}
        self.SDAfterEventEnd = gen_params.get('SDAfterEventEnd',0.25)
        self.MedianPostTriggerReports = gen_params.get('MedianPostTriggerReports',4)
        self.OptimizationInterval = gen_params.get('OptimizationInterval', 300)

        #Adding random generators for determining time for message generation
        random_generator.add_generator_log(self.title + 'After', 0, self.SDAfterEventEnd)
        random_generator.add_generator_poisson(self.title, self.GenerationMeanTime[-1])

        
        #Global Targets
        self.TargetSamplingRate = target_params.get('TargetSamplingRate')

        #Regional Targets
        self.TargetBMMsPerSegment = target_params.get('TargetBMMsPerSegment')
        self.SegmentLength = target_params.get('SegmentLength')

        #Regional DIDC (used only for periodics)
        self.region_based_generation = target_params.get('region_based_generation', False)

        #Targets for an intersection (turning)
        self.TargetBMMsPerIntersection = target_params.get('TargetBMMsPerIntersection')
        self.intersections = None
        if len(turn_params)>0 and len(turn_params['intersections']) >0:
            self.intersections = turn_params['intersections']
            for intersection in self.intersections.keys():
                self.GenerationMeanTime[intersection] = self.GenerationMeanTime[-1]
                random_generator.add_generator_poisson(self.title + intersection, self.GenerationMeanTime[-1])

        #Burst Messages (traction control)
        self.generateBursts = burst_params.get('burst_messages', False)
        if self.generateBursts:
            #List of all burst triggers generated from this trigger
            self.burst_triggers = []
            #Parameters about burst messages
            self.burst_time_length = burst_params.get('burst_time_length', 120)
            self.burst_time_extension = burst_params.get('burst_time_extension', 5.0)
            self.burst_range = burst_params.get('burst_range', 1000)
            self.burst_generation_time = burst_params.get('burst_generation_time', 25)
        
        #None unless this is a burst trigger
        self.expiration_tp = burst_params.get('expiration_tp', None)

        #Queue Estimation parameters
        self.queue_estimation = None        
        if queue_params.get('queue_links'):
            queue_links = queue_params.get('queue_links')
            #a dictionary that holds each queue link and it's information needed for queue estimations
            self.queue_estimation = {}
            for link in queue_links:
                link = int(link)
                self.queue_estimation[link] = {'link_length': link_lengths[link], 'queue_region_length': 100}
                self.GenerationMeanTime[link] = self.GenerationMeanTime[-1]
                random_generator.add_generator_poisson(self.title + str(link), self.GenerationMeanTime[-1])

        #list of links in routes file
        self.links = []

        #Creating random generators for specific regions
        if self.TargetBMMsPerSegment != None and routes != None:
            for route_group in routes:
                for route_num in route_group:
                    for link in routes[route_group][route_num]:
                        
                        self.links.append(link)

                        if self.region_based_generation:
                            self.GenerationMeanTime[link] = self.GenerationMeanTime[-1]
                            random_generator.add_generator_poisson(self.title + str(link), self.GenerationMeanTime[link])


#-------------------------------------------------------------------------           


    def find_next_tp(self, random_generator, veh_data, tp):
        """Finds the next generation time based on the vehicle location.
        :param random_generator: the random generator
        :param veh_data: vehicle data
        :param tp: time
        :return: next message generation time"""
        #if in a regional target link or in queue region
        if (self.region_based_generation and int(veh_data['link']) in self.links) or (self.in_queue_region(veh_data['link'], veh_data['link_x']) != None):
                return tp + (float(random_generator[self.title + str(veh_data['link'])])) / 10.0
        #if in an intersection
        elif self.TargetBMMsPerIntersection != None and self.in_intersection(veh_data['location_x'], veh_data['location_y']):
                return tp + (float(random_generator[self.title + self.in_intersection(veh_data['location_x'],veh_data['location_y'])]) ) / 10.0
        else:
                return tp + (float(random_generator[self.title])) / 10.0
            
#-------------------------------------------------------------------------           

    def find_max_msg_time(self, random_generator, veh_data, tp):
        """Finds the next generation time based on the vehicle location.
        :param random_generator: the random generator
        :param veh_data: vehicle data
        :param tp: time
        :return: expiration time of the after period"""
        rnd = random_generator[self.title + 'After']
        if self.TargetBMMsPerSegment and self.region_based_generation and veh_data['link'] in self.links:
                return tp + floor(float(self.GenerationMeanTime[str(veh_data['link'])]) / 10 \
                        * self.MedianPostTriggerReports \
                        * rnd)
        else:
                return tp + floor(float(self.GenerationMeanTime[-1]) / 10 \
                        * self.MedianPostTriggerReports \
                        * rnd)

#-------------------------------------------------------------------------           
    def active(self, veh_data):
        """Checks if Trigger should be turned on
        :param veh_data: vehicle data
        :return: True if trigger is turned on, otherwise False
        """
        return eval(self.start_trigger)
#-------------------------------------------------------------------------           
    def off(self, veh_data):
        """Checks if active Trigger should be turned off
        :param veh_data: veh_data 
        :return: True if trigger is turned off, otherwise False
        """
        return eval(self.end_trigger)
#-------------------------------------------------------------------------

    def in_queue_region(self, link, link_x):
        """Checks if link, link_x is in a queue region
        :param link: the link the vehicle is on
        :param link_x: the link x location of the vehicle
        :return: link of the queue region if in one. Otherwise None. """
        #Checks if this location is in one of the queue trigger's regions 
        if self.queue_estimation == None or link not in self.queue_estimation.keys():
            return None
        if link_x > (self.queue_estimation[link]['link_length'] - self.queue_estimation[link]['queue_region_length']):
            return link  
#--------------------------------------------------------------------------
    def in_intersection(self, x, y):
        """Checks if x,y are within an intersection region
        :param x: x location (ft)
        :param y: y location (ft)
        :return: Intersection title if in one, else None."""
        for k, v in self.intersections.iteritems():
            if v['x1'] < x < v['x2'] and v['y1'] < y < v['y2']:
                return k
        return None

#-------------------------------------------------------------------------           

class Triggers():


    def __init__(self, regions, RandomGen_seed, routes = None, link_lengths = None):
        """This class holds all the custom triggers
        :param regions: Regions instance
        :param RandomGen_seed: seed value
        :param routes: list of vehicle routes
        :param link_lengths: the lengths of all links
        """
        self.random_generator = Random_generator(RandomGen_seed)
        self.triggers = {}
        self.routes = routes
        self.link_lengths = link_lengths
        self.region_based_generation = False
        
        self.burst_triggers = {}

        self.valid_trigger_list = ['speed','accel_instantaneous', 'yawrate', 'time', 'heading', 'location_x', 'location_y',]
        if regions is not None:
            for Event in regions.Event_titles:
                self.valid_trigger_list.append(Event.replace(' ', ''))
#-------------------------------------------------------------------------           

    def add_Trigger(self, title, start_trigger, end_trigger, BMM_Type, gen_params, target_params, queue_params, burst_params, turning_params):
        """Adds new Trigger instance to Triggers object
        :param title: Trigger title
        :param start_trigger: Expression to turn on trigger
        :param end_trigger: Expression to turn off trigger
        :param BMM_Type: the BMM type associated with the trigger
        :param gen_params: general parameters
        :param target_params: target parameters
        :param queue_params: queue parameters
        :param burst_params: burst parameters
        :param turning_params: turning parameters 
        """

        start_trigger, end_trigger = self.create_expressions(start_trigger, end_trigger)
        self.triggers[title] = Trigger(title, start_trigger, end_trigger, BMM_Type, self.random_generator, 
                                gen_params, target_params, queue_params, burst_params, turning_params, self.link_lengths, self.routes)

    def add_burst_Trigger(self, trigger, random_generator, veh_data, tp):
        """Adds new Burst Trigger instance to Triggers object
        :param trigger: initial trigger
        :param random_generator: the random generator
        :param veh_data: vehicle data
        :param tp: time
        :return: the new burst trigger
        """
        dist = "((veh_data['location_x'] - %s)**2 + (veh_data['location_y'] - %s)**2)**0.5" % (veh_data['location_x'], veh_data['location_y'])
        
        start_trigger = "%s < %s and veh_data['link']== %s and not %s" % (dist, trigger.burst_range, veh_data['link'], trigger.start_trigger)
        end_trigger = "%s > %s or veh_data['link'] != %s or %s" %(dist, trigger.burst_range, veh_data['link'], trigger.start_trigger)

        title = '%s_Burst_%s_%s' % (trigger.title, veh_data['link'], int(veh_data['link_x']))

        t = Trigger(
                        title, start_trigger, end_trigger, trigger.BMM_Type*10, random_generator, 
                        gen_params = {'GenerationMeanTime': trigger.burst_generation_time, 'MedianPostTriggerReports': 0, },
                        burst_params={'expiration_tp': (tp+trigger.burst_time_length), 'burst_time_extension': trigger.burst_time_extension}, 
                    )
     
        trigger.burst_triggers.append(t)
        self.triggers[title] = t

        return t

#-------------------------------------------------------------------------           

    def modify(self, expression):
        """Modifies user input expressions
        :param expression: start or end trigger expression to be modfied
        :return: modified expression
        """
        expression = expression.lower().replace(' ', '')

        if '=' in expression and ('==' not in expression and '>=' not in expression and '<=' not in expression):
                expression = expression.replace('=', '==')
        
        if 'false' in expression:
            expression = expression.replace('false', '0')
        if 'true' in expression:
            expression = expression.replace('true', '1')
        if 'on' in expression:
            expression = expression.replace(' on ', ' 1 ')
        if 'off' in expression:
            expression = expression.replace(' off ', '0')
        
        # Replace various wordings of acceleration with 'accel_instantaneous'
        if 'acceleration' in expression:
            expression = expression.replace('acceleration', 'accel_instantaneous')

        elif 'Acceleration' in expression:
            expression = expression.replace('Acceleration', 'accel_instantaneous')

        elif 'Accel' in expression:
            expression = expression.replace('Accel', 'accel_instantaneous')

        elif 'accel' in expression:
            expression = expression.replace('accel', 'accel_instantaneous')

        for valid_trigger in self.valid_trigger_list:
            if valid_trigger.lower() in expression:
                expression = expression.replace(valid_trigger.lower(), valid_trigger)
        return expression
#-------------------------------------------------------------------------           

    def check_new(self, veh_data):
        """Checks if new triggers have been turned on
        :param veh_data: vehicle to check
        :return: A list of the newly activated triggers
        """
        activated_triggers = []

        for title, trigger in self.triggers.iteritems():
            #Find one active burst trigger
            if trigger.generateBursts:
                active_bursts = len([trigger for burst_trigger in trigger.burst_triggers if burst_trigger in veh_data['active_triggers']]) > 0 

                if active_bursts == False:
                    for burst_trigger in trigger.burst_triggers:
                        if burst_trigger.active(veh_data):
                            activated_triggers.append(burst_trigger)
                        break
            #Find all active triggers that are not burst triggers
            if trigger.active(veh_data) and trigger not in veh_data['active_triggers'] and trigger.expiration_tp == None:
                    activated_triggers.append(trigger)
        return activated_triggers
#-------------------------------------------------------------------------           

    def check_off(self, veh_data):
        """Checks if active triggers have been turned off
        :param veh_data: vehicle to check
        :return: list of turned off triggers
        """
        turned_off_triggers = []
        for trigger in veh_data['active_triggers']:
            if trigger.off(veh_data):
                turned_off_triggers.append(trigger)
        return turned_off_triggers

#-------------------------------------------------------------------------           
    def remove_expired_triggers(self, tp, veh_data):
        """Removes all expired burst triggers from their initial trigger's burst message list and also from the Triggers dictionary of triggers.
        :param veh_data: vehicle data
        :param tp: time
        """
        #remove expired trigger from triggers list, and from initial trigger's burst trigger list
        to_remove = []
        for title, trigger in self.triggers.iteritems():
            if trigger.generateBursts:
                to_remove = [burst_trigger for burst_trigger in trigger.burst_triggers if burst_trigger.expiration_tp < tp]
                for burst_trigger in to_remove:
                    trigger.burst_triggers.remove(burst_trigger)
        
        for burst_trigger in to_remove:
            self.triggers.pop(burst_trigger.title)

        #remove expired triggers from veh's active trigger list
        expired = [trigger for trigger in veh_data['active_triggers'].keys() if trigger.title not in self.triggers.keys()]
        for trigger in expired:
            veh_data['active_triggers'].pop(trigger)
    
#-------------------------------------------------------------------------           

    def create_expressions(self, start_trigger, end_trigger):
        """Creates statements that are able to be evaluated from user input
        :param start_trigger: user input start_trigger
        :param end_trigger: user input end_trigger
        :return: start and end expressions to be evaluated
        """
        s = start_trigger
        e = end_trigger
        
        s= s.replace('and', ' and ')
        s = s.replace('or', ' or ')

        e = e.replace('and', ' and ')
        e = e.replace('or', ' or ')

        for valid_trigger in self.valid_trigger_list:
            if valid_trigger in s:
                s = string.replace(s, valid_trigger, "veh_data['" + valid_trigger + "']")
            if valid_trigger in e:
                e = string.replace(e, valid_trigger, "veh_data['" + valid_trigger + "']")
        print s
        return s, e
#-------------------------------------------------------------------------           

    def check_logic_errors(self, start_trigger, end_trigger):
        start_split = re.split('\W', start_trigger)
        end_split = re.split('\W', end_trigger)
        error_list = []

        if 'speed' in start_trigger and 'speed' in end_trigger:
            if float(start_split[-1]) > float(end_split[-1]):
                error_list.append('Speed trigger values invalid - End speed trigger of %s is less than start speed trigger of %s' % (end_split[-1], start_split[-1]))

        if start_split[-1] == '-9999' or end_split[-1] == '-9999':
            error_list.append('Invalid trigger value of -9999 found for %s trigger' % (start_split[0]))

        return error_list
#-------------------------------------------------------------------------           
            
    def check_errors(self, trigger_title, start_trigger, end_trigger):
        """Check if there are errors in user defined triggers
        :param trigger_title: trigger title
        :param start_trigger: start trigger expression
        :param end_trigger: end trigger expression
        :return: list of errors
        """
        error_list = []
        
        #Checks for multiple statements
        start_statements = start_trigger.replace('and', '//').replace('or', '//').split('//')
        end_statements = end_trigger.replace('and', '//').replace('or', '//').split('//')


        for start in start_statements:
            start_split = re.split('\W', start_trigger)
            start_valid_element =   False
            start_valid_operand = False

            for operand in ['<', '>','<=','>=','==', '!=',]:
                if operand in start:
                    start_valid_operand = True
            
            for s in start_split:
                if s in self.valid_trigger_list:
                        start_valid_element = True

            if start_valid_element == False:
                error_list.append('Start trigger has no valid trigger variable: %s ' % start_trigger)
            if start_valid_operand == False:
                error_list.append('Start trigger statement not able to be evaluated: %s' % start_trigger)



        for end in end_statements:
            end_split = re.split('\W', end_trigger)

            end_valid_element = False
            end_valid_operand = False

            if '=' in end and ('==' not in end and '<=' not in end and '>=' not in end):
                end = end.replace('=', '==')


            for operand in ['<', '>','<=','>=','==', '!=',]:
                if operand in end:
                    end_valid_operand = True
            for e in end_split:
                if e in self.valid_trigger_list:
                    end_valid_element = True

            if end_valid_element == False:
                error_list.append('End trigger has no valid trigger variable: %s ' % end_trigger)
            if end_valid_operand == False:
                error_list.append('End trigger statement not able to be evaluated: %s' % end_trigger)

        
        if len(error_list) == 0:
            error_list.extend( self.check_logic_errors(start_trigger, end_trigger) )

        return error_list
#-------------------------------------------------------------------------           

    def write(self):
        if len(self.triggers) < 1:
            print "No triggers"

        else:
            for trigger in self.triggers:
                print "Trigger: %s, Start: %s, End: %s, GenerationMeanTime: %s, SDAfterEventEnd: %s, MedianPostTriggerReports: %s" % (trigger.title, 
                    trigger.start_trigger, trigger.end_trigger, trigger.GenerationMeanTime, trigger.SDAfterEventEnd, trigger.MedianPostTriggerReports)
#-------------------------------------------------------------------------           

def int_check(value, key):
    """Cast a value as an integer
    :param value: The value to cast as int
    :param key: The value name
    :return: The value as an integer, otherwise an error message
    """

    try:
        int(value)
        return int(value), ''
    except:
        return None, 'Error: %s value must be a integer' % (key)

#-------------------------------------------------------------------------           

def boolean_check(value, key):
    """Cast a value as an integer
    :param value: The value to cast as boolean
    :param key: The value name
    :return: The value as an integer, otherwise an error message
    """

    if value.lower() == 'true' or value == '1':
        return True
    else:
        return False

#-------------------------------------------------------------------------           

def float_check(value, key):
    """Cast a value as a float
    :param value: The value to cast as a float
    :param key: The name of the value
    :return: The value as a float, otherwise an error message
    """

    try:
        float(value)
        return float(value), ''
    except:
        return None, 'Error: %s value must be a float' % (key)

#-------------------------------------------------------------------------           

def Load_DIDC_Parameters(DIDC_File, regions, RandomGen_Seed, PeriodicGMTFile):
    """Load DIDC File
    :param DIDC_File: DIDC filename
    :param regions: Regions instance
    :return: Dictionary with all DIDC Parameters and Triggers 
    """
    try:
        tree = ET.parse(DIDC_File)
        root = tree.getroot()
    except:
            logger.info("Error: cannot find or invalid format for DIDC Parameters file %s" % DIDC_File)
            print
            raise

    DIDC_Parameters = {
            'BMMTransmissionThreshold' : [4, 'Default', '', 'int', 'TransmissionThreshold'], # Ranges from 4 to 32 BMMs
            'MessageSize' : [39, 'Default', '','int', 'MessageSize'],
        }
    DIDC = {}

    for key, value in DIDC_Parameters.iteritems():

            if root.find(value[4]) != None:

                if value[3] == 'int':
                        DIDC_Parameters[key][0], DIDC_Parameters[key][2] = int_check(root.find(value[4]).text, key)
                elif value[3] == 'file':
                    DIDC_Parameters[key][0]  = self.file_check(root.find(value[4]).text)
                elif value[3] == 'float':
                        DIDC_Parameters[key][0], DIDC_Parameters[key][2] = float_check(root.find(value[4]).text, key)
                else:
                    DIDC_Parameters[key][0] = root.find(value[4]).text

                DIDC_Parameters[key][1] = 'User_Defined'

            DIDC[key] = DIDC_Parameters[key][0]

    DIDC['Triggers'], DIDC['error_list'] = Load_Triggers(root, regions, RandomGen_Seed, PeriodicGMTFile)
    return DIDC
#-------------------------------------------------------------------------           

def Load_Triggers(root, regions, RandomGen_Seed, PeriodicGMTFile):
    """Load the Triggers in the DIDC Parameters File
    :param root: root of DIDC Parameters File
    :return: The Triggers object
    """
    if root.find('RoutesFile') is not None and root.find('LinkLengthsFile') is not None:
        routes_filename = root.find('RoutesFile').text.strip()
        lengths_filename = root.find('LinkLengthsFile').text.strip()
        routes = read_full_routes(routes_filename)
        link_lengths = read_link_length(lengths_filename)
        T = Triggers(regions, RandomGen_Seed, routes, link_lengths)

    else: 
        T = Triggers(regions, RandomGen_Seed)

    if root.find('Triggers') is not None:
        root = root.find('Triggers')
        
        error_list = []
        BMM_Types = []
        t = 0

        
        for trigger in root.findall('Trigger'):
            trigger_title = trigger.find('Title').text.strip()

            start_trigger = trigger.find('Start').text

            end_trigger = trigger.find('End').text

            BMM_Type = int(trigger.find('Type').text)
            

            gen_params = {'GenerationMeanTime': [50, 'Default', '', 'int', 'GenerationMeanTime'],
                            'SDAfterEventEnd' : [0.25, 'Default', '', 'float', 'SDAfterEventEnd'],
                            'MedianPostTriggerReports': [4, 'Default', '', 'int', 'MedianPostTriggerReports'],
                            'OptimizationInterval' : [300, 'Default', '', 'int', 'OptimizationInterval'],
                             }

            target_params = { 'TargetSamplingRate': [None,'Default', '', 'int', 'Targets/GlobalTargets/TargetSamplingRate'],
                                'TargetBMMsPerSegment': [None,'Default', '', 'int', 'Targets/RegionalTargets/TargetBMMsPerSegment'],
                                'SegmentLength' : [None, 'Default', '', 'int', 'Targets/RegionalTargets/SegmentLength'],
                                'region_based_generation': [False, 'Default', '', 'boolean', 'Targets/RegionalTargets/RegionalDIDC'],
                                'TargetBMMsPerIntersection':[None, 'Default', '', 'int', 'Targets/IntersectionTargets/TargetBMMsPerIntersection'], }
            queue_params = { 'queue_links': [None, 'Default', '', 'List_int', 'QueueEstimation/Links'] }

            burst_params = {
                            'burst_messages': [False, 'Default', '', 'boolean', ''],
                            'burst_time_length': [120, 'Default', '', 'float', 'BurstMessages/BurstTimeLength'],
                            'burst_time_extension': [5.0, 'Default', '', 'float', 'BurstMessages/BurstTimeExtension'],
                            'burst_range': [1000, 'Default', '', 'int', 'BurstMessages/BurstRange>'],
                            'burst_generation_time': [25, 'Default', '', 'int', 'BurstMessages/BurstGenerationTime'],
                            }

            trigger_params = [gen_params, target_params, queue_params, burst_params]

            relevant_params = [gen_params]
            if trigger.find('Targets') != None:
                relevant_params.append(target_params)
            if trigger.find('QueueEstimation') != None:
                relevant_params.append(queue_params)
            if trigger.find('BurstMessages') != None:
                burst_params['burst_messages'][0]= True
                relevant_params.append(burst_params)
            
            #Find All Intersections
            turn_params = {}
            intersections = {}
            METERS_TO_FEET = 100 / 2.54 / 12

            if trigger.find('IntersectionRegions') != None:
                for intersection in trigger.findall('IntersectionRegions/Intersection'):
                    title = intersection.find('Title').text
                    x_values = [int(x) * METERS_TO_FEET for x in intersection.find('x').text.split(',')]
                    y_values = [int(y) * METERS_TO_FEET for y in intersection.find('y').text.split(',')]
                    
                    if intersection.find('TargetIntersectionSamplingRate') != None:
                        target = int(intersection.find('TargetIntersectionSamplingRate').text)
                    else:
                        target = 300
                    
                    intersections[title] = {'x1': min(x_values), 'x2': max(x_values), 'y1': min(y_values), 'y2': max(y_values)}

            turn_params['intersections'] = intersections


            #Finds all relevant parameters, if not found, set as default.
            for params in trigger_params:
                if params in relevant_params:
                    for key, value in params.iteritems():
                        #set as user input
                        if trigger.find(value[4]) != None:
                                if value[3] == 'int':
                                    params[key], error = int_check(trigger.find(value[4]).text, key)
                                elif value[3] == 'float':
                                    params[key], error = float_check(trigger.find(value[4]).text, key)
                                elif value[3] == 'List_int':
                                    params[key] = str(trigger.find(value[4]).text).split(',')
                                elif value[3] == 'boolean':
                                    params[key] = boolean_check(trigger.find(value[4]).text, key)
                                else:
                                    params[key] = trigger.find(value[4]).text
                        
                                if error:
                                    error_list.append(error)
                        #set as default
                        else:
                            params[key] = value[0]

                #for all other parameters, set as default
                else:
                    for key, value in params.iteritems():
                        params[key] = value[0] 

            # If there are Periodic BMMs, write the generation mean times to file 
            if trigger_title == 'Periodic':
                curdir = os.path.dirname(os.path.realpath(__file__)) + os.sep
                gmt_file = curdir + PeriodicGMTFile
                with open(gmt_file, 'wb') as out_f:
                    out_f.write('Time,GMT(deciseconds)\n0,%s\n' % (trigger_params[0]['GenerationMeanTime']))


            start_trigger = T.modify(start_trigger)
            end_trigger = T.modify(end_trigger)

            error_str = T.check_errors(trigger_title, start_trigger, end_trigger)
            error_list.extend(error_str)

            if len(error_str) < 1:
                T.add_Trigger(trigger_title, start_trigger,end_trigger, BMM_Type, gen_params, target_params, queue_params, burst_params, turn_params)

        if len(error_list) > 0:
            print error_list
            with open('TCA_DIDC_Trigger_Errors.csv', 'wb') as f_out:
                f_out.write('DIDC Trigger Value Errors\n')
                f_out.write('\n'.join(error_list))
                f_out.write('\n\n')
                f_out.write('Allowed trigger elements based on your regions file are:')
                f_out.write(' '.join(T.valid_trigger_list))

        return T, error_list 
#-------------------------------------------------------------------------           
                    
def read_full_routes(filename):
    routes = {}

    with open(filename) as f:
        next(f) #Skip header line

        for line in f:
            row = line.strip().split(',')
            route_group = row[0]
            route = row[1]

            if route_group not in routes.keys():
                routes[route_group] = {}

            if route not in routes[route_group].keys():
                routes[route_group][route] = []

            for col in range(4,len(row)):
                if row[col] == '':
                    break
                routes[route_group][route].append(int(row[col]))

    return routes
#-----------------------------------------------------------------------

def read_link_length(filename):
    link_lengths = {}

    with open(filename) as f:
        next(f) #Skip header line

        for line in f:
            row = line.strip().split(',')
            link = int(row[0])
            length = float(row[1])
            link_lengths[link] = length

    return link_lengths

#*************************************************************************
class TriggersTest(unittest.TestCase):

    def setUp(self):
        with open("test_TCA_Triggers_good.xml", 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
                            <DIDC>
                                <Title> DIDC File </Title>
                                <RoutesFile>Example_DIDC/pcn_full_route.csv</RoutesFile>
                                <LinkLengthsFile>Example_DIDC/pcn_link_lengths.csv</LinkLengthsFile>
                                <Triggers>
                                    <Trigger>
                                        <Title>Queue Trigger</Title>
                                        <Start>speed &lt; 6</Start>
                                        <End>speed &gt;= 10</End>
                                        <Type>1</Type>
                                        <GenerationMeanTime>50</GenerationMeanTime>
                                        <SDAfterEventEnd>0.5</SDAfterEventEnd>
                                        <MedianPostTriggerReports>4</MedianPostTriggerReports>
                                    </Trigger>
                                </Triggers>)
                            </DIDC>""")
        with open("test_TCA_Triggers_bad_1.xml", 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
                            <DIDC>    
                                <Triggers>
                                    <Trigger>
                                        <Title>Queue Trigger</Title>
                                        <Start>speeed &lt; 1</Start>
                                        <End>speed &gt;= 10</End>
                                        <Type>1</Type>
                                        <GenerationMeanTime>50</GenerationMeanTime>
                                        <SDAfterEventEnd>0.5</SDAfterEventEnd>
                                        <MedianPostTriggerReports>4</MedianPostTriggerReports>
                                    </Trigger>
                                    <Trigger>
                                        <Title>Traction Control</Title>
                                        <Start>Traction Control = 1</Start>
                                        <End>TractionControl = 0</End>
                                        <Type>2</Type>
                                        <GenerationMeanTime>five</GenerationMeanTime>
                                        <SDAfterEventEnd>0.5</SDAfterEventEnd>
                                        <MedianPostTriggerReports>4</MedianPostTriggerReports>
                                    </Trigger>
                                </Triggers>
                            </DIDC>""")

        with open("test_TCA_Triggers_bad_2.xml", 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
                            <DIDC>
                                <Triggers>
                                    <Trigger>
                                        <Title>Queue Trigger</Title>
                                        <Start>speed &lt; 10</Start>
                                        <End>speed &gt;= 5</End>
                                        <Type>1</Type>
                                        <GenerationMeanTime>50</GenerationMeanTime>
                                        <SDAfterEventEnd>0.5</SDAfterEventEnd>
                                        <MedianPostTriggerReports>4</MedianPostTriggerReports>
                                    </Trigger>
                                </Triggers>
                            </DIDC>""")

        with open('test_TCA_Regions.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?> 
                            <Regions> 
                                <Cell_Regions>
                                  <DefaultLossPercent>2</DefaultLossPercent>
                                  <DefaultLatency>1</DefaultLatency>    
                                  <MinPDMtoTransmit>1</MinPDMtoTransmit>
                                </Cell_Regions>
                                <Event_Regions>
                                    <Region>
                                      <Title>HeavyRain</Title>      
                                      <UpperLeftPoint>
                                        <X>-5624</X>
                                        <Y>-1914</Y>
                                      </UpperLeftPoint>
                                      <LowerRightPoint>
                                        <X>-4917</X>
                                        <Y>-3185</Y>          
                                      </LowerRightPoint>  
                                      <TimePeriods>
                                          <Period>
                                            <StartTime>0</StartTime> 
                                            <EndTime>400</EndTime>
                                          </Period>
                                      </TimePeriods> 
                                      <Events>
                                          <Event>
                                            <Title>TractionControl</Title>
                                            <Probability>30</Probability>
                                            <Recheck>5</Recheck>
                                          </Event>
                                      </Events>      
                                    </Region>
                                </Event_Regions>        
                            </Regions>""")

 #-------------------------------------------------------------------------           
       
    def test_good_trigger_file(self):
        R = Load_Regions('test_TCA_Regions.xml', 123456, 1)

        DIDC = Load_DIDC_Parameters('test_TCA_Triggers_good.xml', R, 123456, 'test')
        T = DIDC['Triggers']
        error_list = DIDC['error_list']

        veh_data = {'speed': 9, 'active_triggers': {}}
        active_triggers = T.check_new(veh_data)
        assert len(active_triggers) == 0
        veh_data['speed'] = 0.9

        active_triggers = T.check_new(veh_data)
        assert len(active_triggers) == 1
#-------------------------------------------------------------------------           

    def test_bad_trigger_file_1(self):
        R = Load_Regions('test_TCA_Regions.xml', 123456, 1)

        DIDC = Load_DIDC_Parameters('test_TCA_Triggers_bad_1.xml', R, 123456, 'test')
        T = DIDC['Triggers']
        error_list = DIDC['error_list']

        assert(len(error_list) == 2)
#-------------------------------------------------------------------------           

    def test_bad_trigger_file_2(self):
        R = Load_Regions('test_TCA_Regions.xml', 123456, 1)

        DIDC = Load_DIDC_Parameters('test_TCA_Triggers_bad_2.xml', R, 123456, 'test')
        T = DIDC['Triggers']
        error_list = DIDC['error_list']


        assert(len(error_list) == 1)

#-------------------------------------------------------------------------           

    def tearDown(self):
        import os
        os.remove('test_TCA_Triggers_good.xml')
        os.remove('test_TCA_Triggers_bad_1.xml')
        os.remove('test_TCA_Triggers_bad_2.xml')
        os.remove('test_TCA_Regions.xml')
#*************************************************************************

if __name__ == '__main__':
    unittest.main()

