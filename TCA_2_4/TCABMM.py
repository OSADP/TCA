#standard
from math import floor
import sys

#external
import pandas as pd


#TCA
from TCACore import Timer, logger, report_errors
from TCARandom import Random_generator
from TCATriggers import Load_DIDC_Parameters

class BMM(object):

    def __init__(self, RandomGen_seed, CF, regions, msg_limit = 800000):

        """
        Initializes a BMM module

        :param RandomGen_seed: The random seed
        """
        # self.random_generator = Random_generator(RandomGen_seed)
        self.CF = CF
        self.regions = regions
        self.timer = Timer(enabled=True)

        self.BMM_list = []
        self.BMMBuffer = BMMBuffer()
        self.Triggers = None

        # key: bmm type, value: trigger title
        self.BMM_Type = {}

        self.event_count = {}
        self.turning_event_count = {}

        self.EventStatus = {
            'Off' : 0,
            'On' : 1,
            'After' : 2,
        }

        self.headerBMM = True
        self.BMM_col_order = ['DSRC_MessageID',
                            'Vehicle_ID',
                            'transtime',
                            'localtime',
                            'x',
                            'y',
                            'link',
                            'link_x',
                            'spd',
                            'heading',
                            'yawrate',
                            'accel',
                            'brakeStatus',
                            'brakePressure',
                            'hardBraking',
                            'transTo',
                            'BMM_Type',
                            'length',
                            'width',]
        #Limit of message list before printing to a file
        self.msg_limit = msg_limit


        if CF.Control['DIDCParametersFile']:
            if self.CF.Control["OutputLevel"] >= 1:
                logger.info("Loading DIDC Parameters values File %s" % (self.CF.Control["DIDCParametersFile"]))
            self.DIDC = Load_DIDC_Parameters(CF.Control['DIDCParametersFile'], self.regions, RandomGen_seed, CF.Control['PeriodicGMTFile'])
            self.Triggers = self.DIDC['Triggers'] 
               
            if len(self.DIDC['error_list']) > 0:
                logger.info('Errors in DIDC Parameters file - See TCA_DIDC_Trigger_Errors.csv for details')
                sys.exit()

            for title, trigger in self.Triggers.triggers.iteritems():
                self.BMM_Type[trigger.BMM_Type] = title

        self.FT_CONVERSION = 12 * 2.54 / 100 # converts feet to meters
        self.ACCEL_CONVERSION = 1 / 32.1740485564 # converts ft/s2 to g

        if self.regions is not None:
            for Event in self.regions.Event_titles:
                self.BMM_col_order.append(Event)


        self.burst_extensions = {}

#-------------------------------------------------------------------------                    
    def Check(self, veh_data, tp):

        self.timer.start('TCABMM - remove_expired_triggers')
        self.Triggers.remove_expired_triggers(tp, veh_data)
        self.timer.stop('TCABMM - remove_expired_triggers')

        self.timer.start('TCABMM - check_new')
        turned_on_triggers = self.Triggers.check_new(veh_data)
        self.timer.stop('TCABMM - check_new')
        
        self.timer.start('TCABMM - check_off')
        turned_off_triggers = self.Triggers.check_off(veh_data)
        self.timer.stop('TCABMM - check_off')

        for title, trigger in self.Triggers.triggers.iteritems():
            #if off or after
            if trigger not in veh_data['active_triggers']:  
                self.timer.start('TCABMM - Check new triggers')              
                
                if trigger in turned_on_triggers:
                    if trigger in veh_data['after_triggers']:
                        veh_data['after_triggers'].pop(trigger)
                    veh_data['active_triggers'][trigger] = {'next_tp': trigger.find_next_tp(self.Triggers.random_generator, veh_data, tp)}
                    self.Generate(veh_data, trigger.BMM_Type)

                    #=========================================
                    if trigger.title in self.event_count.keys():
                        self.event_count[trigger.title] +=1
                    else:
                        self.event_count[trigger.title] = 1
                    
                    if trigger.title == 'Turning':
                        region = trigger.in_intersection(veh_data['location_x'], veh_data['location_y'])
                        if region in self.turning_event_count:
                            self.turning_event_count[region] +=1
                        else:
                            self.turning_event_count[region] = 1
                    #==========================================

                    if self.CF.Control["OutputLevel"] >= 2:
                        logger.debug('%s Event Start for vehicle ID: %s at time: %s' % (title, veh_data['vehicle_ID'], veh_data['time']))
                    
                    self.timer.stop('TCABMM - Check new triggers')


                #if after
                elif trigger in veh_data['after_triggers']:
                    self.timer.start('TCABMM - Check after triggers')
                    if veh_data['after_triggers'][trigger]['max_msg_time'] <= tp:
                        veh_data['after_triggers'].pop(trigger)
                        
                        if self.CF.Control["OutputLevel"] >= 2:
                            logger.debug('%s Event After Case Ended for vehicle ID: %s at time: %s' % (title, veh_data['vehicle_ID'], veh_data['time']))

                    elif veh_data['after_triggers'][trigger]['next_tp'] <= tp:
                        self.Generate(veh_data, trigger.BMM_Type)
                        veh_data['after_triggers'][trigger]['next_tp'] = trigger.find_next_tp(self.Triggers.random_generator, veh_data, tp)
                    self.timer.stop('TCABMM - Check after triggers')
            else: 
                #if on
                self.timer.start('TCABMM - Check current triggers')
                if veh_data['active_triggers'][trigger]['next_tp'] <= tp:
                    self.Generate(veh_data, trigger.BMM_Type)
                    veh_data['active_triggers'][trigger]['next_tp'] = trigger.find_next_tp(self.Triggers.random_generator, veh_data, tp)

               
                #if turned off       
                if trigger in turned_off_triggers:
                    if trigger.MedianPostTriggerReports > 0:
                        veh_data['after_triggers'][trigger] = veh_data['active_triggers'].pop(trigger)
                        veh_data['after_triggers'][trigger]['max_msg_time'] = trigger.find_max_msg_time(self.Triggers.random_generator, veh_data, tp)
                        
                        if self.CF.Control["OutputLevel"] >= 2:
                            logger.debug('%s Event End for vehicle ID: %s at time: %s and speed: %s End Time: %s'
                                         % (title, veh_data['vehicle_ID'], veh_data['time'], veh_data['speed'], str(veh_data['after_triggers'][trigger]['max_msg_time'])) )
                    else:
                        veh_data['active_triggers'].pop(trigger)
                        if self.CF.Control['OutputLevel'] >= 2:  
                            logger.debug('%s Event End for vehicle ID: %s at time: %s and speed:%s' % (title, veh_data['vehicle_ID'], veh_data['time'], veh_data['speed']))

                self.timer.stop('TCABMM - Check current triggers')
        template = 'TP: {0:8} {1:40} Link: {2:5} Link_X: {3:8,.0f} End TP: {4:8} Veh: {5:8}'
        for trigger in turned_on_triggers:
            #Check for burst messaging
            # if len(turned_on_triggers) > 0:
            #     print [t.title for t in turned_on_triggers]

            if trigger.generateBursts:
                self.timer.start('TCABMM - Check bursts')
                burst_active = False
                for burst_trigger in trigger.burst_triggers:
                    # If burst is in the vehicle's list of active triggers or the vehicle is within range of the active burst
                    if burst_trigger in veh_data['active_triggers'] or eval(burst_trigger.start_trigger.rsplit('and',1)[0]):
                        # Extend the time of the active burst
                        burst_trigger.expiration_tp+= trigger.burst_time_extension
                        burst_active = True

                        self.burst_extensions[burst_trigger][0] +=1
                        self.burst_extensions[burst_trigger][2] = burst_trigger.expiration_tp

                        if self.CF.Control["OutputLevel"] >= 2:
                            logger.debug(template.format(tp, 'Extended ' + burst_trigger.title, veh_data['link'], veh_data['link_x'], burst_trigger.expiration_tp,veh_data['vehicle_ID']) )
                        break
                # If burst not in the list of active triggers or vehicle not in range of an existing burst of the same trigger type
                if not burst_active:
                    # Create a new burst
                    t = self.Triggers.add_burst_Trigger(trigger, self.Triggers.random_generator, veh_data, tp)
                    self.BMM_Type[t.BMM_Type] = t.title
                    self.burst_extensions[t] = [0, tp, t.expiration_tp]

                    if self.CF.Control["OutputLevel"] >= 2:
                        logger.debug(template.format(tp, 'Created ' + t.title, veh_data['link'], veh_data['link_x'], t.expiration_tp, veh_data['vehicle_ID']) )

                self.timer.stop('TCABMM - Check bursts')



                        
#-------------------------------------------------------------------------
    def recreateRandomGenerator(self, trigger, link=None):
        # if (link and trigger.queue_estimation != None) or trigger.region_based_generation:
        if link != None and link != -1:
            self.Triggers.random_generator.add_generator_poisson(trigger.title + str(link), trigger.GenerationMeanTime[link])
        else:
            self.Triggers.random_generator.add_generator_poisson(trigger.title, trigger.GenerationMeanTime[-1])


#-------------------------------------------------------------------------
    def Generate(self, veh_data, BMM_Type):
        # Create BMM (BSM fields)
        BMM = {
                'Vehicle_ID' : veh_data['vehicle_ID'],
                'localtime' : veh_data['time'],
                'spd' : veh_data['speed'],
                'x' : veh_data['location_x'],
                'y' : veh_data['location_y'],
                'link': veh_data['link'],
                'link_x': veh_data['link_x'],
                'transtime' : 0,
                'transTo' : None, 
                'avg_accel' : veh_data['average_acceleration'],
                'brakeStatus' : veh_data["brake_status"],
                'brakePressure' : veh_data['brake_pressure'],
                'hardBraking' : veh_data['hard_braking'],
                'heading' : veh_data['heading'],
                'BMM_Type' : BMM_Type,
                'yawrate' : veh_data['yawrate'],
                'length' : veh_data['length'],
                'width' : veh_data['width'],
                }
                
        if veh_data['accel_instantaneous'] != None:
            BMM["instant_accel"] = veh_data['accel_instantaneous']

        if self.regions is not None:
            for region_name in self.regions.Event_titles:
                BMM[region_name] = veh_data[region_name]

        # Add BMM to buffer
        self.BMMBuffer.Add(BMM)


        if self.CF.Control["OutputLevel"] >= 2:
            logger.debug('%s BMM generated for vehicle ID: %s at time: %s'
                % (self.BMM_Type[BMM_Type], veh_data['vehicle_ID'], veh_data['time']))
        

#-------------------------------------------------------------------------

    def Write(self, clear_all=False):

        if (len(self.BMM_list) >= self.msg_limit) or clear_all:
            df = pd.DataFrame(self.BMM_list)
            df = df.sort(['transtime', 'Vehicle_ID'])

            if 'instant_accel' in list(df):
                df.rename(columns={'instant_accel': 'accel'}, inplace = True)
            else:
                df['avg_accel'] = df['avg_accel'].fillna(-9999.0)
                df.rename(columns={'avg_accel': 'accel'}, inplace = True)

            df['heading'] = df['heading'].fillna(-9999.0)
            df['accel'] = df['accel'].map(lambda x: '%.3f' % x)
            df['spd'] = df['spd'].map(lambda x: '%.3f' % x)
            df['heading'] = df['heading'].map(lambda x: '%.1f' % x)
            df['DSRC_MessageID'] = '{0:0>2}'.format(2)

            #reorder data elements
            df = df[self.BMM_col_order]

            df.rename(columns={
             'Vehicle_ID': 'Vehicle_ID',
             'localtime': 'Time_Taken',
             'accel': 'Acceleration',
             'heading': 'Heading',
             'spd': 'Speed',
             'x': 'X',
             'y': 'Y',
             'yawrate': 'YawRate',
             'length': 'Vehicle Length(ft)',
             'width': 'Vehicle Width(ft)',
             }, inplace=True)

            df.to_csv(path_or_buf = self.CF.Control["BMMTransFile"],
                           index=False,
                           mode='a',
                           header = self.headerBMM,
                            )
            self.headerBMM = False
            self.BMM_list = []


#-------------------------------------------------------------------------

class BMMBuffer:
#-------------------------------------------------------------------------
    def __init__(self):
        """
        Initializes BMMBuffer module

        """
        self.ActiveBuffers = {}

#-------------------------------------------------------------------------
    def Add(self, BMM):
        """
        Adds BMM message to buffer.

        :param SPOT: The dictionary containing BMM message data
        """
        vehicleID = BMM['Vehicle_ID']

        if vehicleID not in self.ActiveBuffers.keys():
            self.ActiveBuffers[vehicleID] = []

        self.ActiveBuffers[vehicleID].append(BMM)


#-------------------------------------------------------------------------
    def GetBufferSize(self, vehicle_ID):
        if vehicle_ID not in self.ActiveBuffers.keys():
            return 0
        return len(self.ActiveBuffers[vehicle_ID])

#-------------------------------------------------------------------------

    def Transmit(self, vehicle_ID, tp, RSE = None):
        """
        "Transmits" BMM messages in given vehicle's buffer

        :param veh_data: The vehicle transmitting messages
        :return: A list of transmitted BMMs
        """
        BMMs = self.ActiveBuffers[vehicle_ID]

        self.ClearBuffer(vehicle_ID)

        for BMM in BMMs:
            BMM['transtime'] = tp
            if RSE == None:
                BMM['transTo'] = 'cellular'
            else:
                BMM['transTo'] = RSE

        return BMMs

#-------------------------------------------------------------------------

    def ClearBuffer(self, vehicleID):
        """
        Empties the buffer lists of a given vehicle

        :param vehicleID: The vehicle whose buffers are to be cleared
        """
        self.ActiveBuffers[vehicleID] = []


