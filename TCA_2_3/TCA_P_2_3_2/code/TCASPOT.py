#external
import pandas as pd

#TCA
from TCABuffer import CLBuffer, SPOTBuffer
from TCACore import Timer, logger, Get_Heading_Change, SPOT_time
from TCARandom import Random_generator

class SPOT(object):

    def __init__(self, RandomGen_seed, CF, SPOT_tree, msg_limit = 800000):

        """
        Initializes an ITS Spot module

        :param RandomGen_seed: The random seed
        """
        self.random_generator = Random_generator(RandomGen_seed)
        self.CF = CF

        self.Travelmsgs = []
        self.BehaviorMsgs = []
        self.SPOT_tree = SPOT_tree
        self.SPOTBuffer = SPOTBuffer()

        self.header = True
        self.Travel_col_order = ['localtime', 'vehicle_ID', 'x', 'y', 'spd']
        self.Behavior_col_order = self.Travel_col_order + ['accel', 'heading', 'yawrate']
        #Limit of message list before printing to a file
        self.msg_limit = msg_limit

        self.FT_CONVERSION = 12 * 2.54 / 100 # converts feet to meters
        self.ACCEL_CONVERSION = 1 / 32.1740485564 # converts ft/s2 to g
        self.SPOT_SPD_CONVERSION = 1.609344 # converts mph to km/hr for ITS Spot Output
        self.SPOT_accel_threshold = self.CF.Strategy['SPOTaccelThreshold'] * 32.1740485564 # Convert g to ft/s^2 for ITS Spot Output
        self.SPOT_yawrate_threshold = self.CF.Strategy['SPOTyawrateThreshold'] * 32.1740485564 # Convert g to ft/s^2 for ITS Spot Output

#-------------------------------------------------------------------------
    def CheckTravelRecords(self, veh_data):
        """
        Checks to see if the vehicle has triggered any of the requirements for producing an ITS Spot travel record

        :param veh_data: The vehicle data of the vehicle transmitting the message
        :return: True if the vehicle triggers an ITS Spot Travel Record, false otherwise
        """


        # Travel Records: Check that vehicle has traveled 200m since the beginning or since the last ITS Spot or changed heading by 45 degrees

        if veh_data['prev_tp_travel_SPOT'] is None and (veh_data['total_dist_traveled'] * self.FT_CONVERSION) >= 200: #convert feet to meters
            if self.CF.Control['OutputLevel'] >= 2:
                logger.debug('Travel SPOT generated at time: %s for vehicle ID: %s because initial distance traveled of: %s meters' % (veh_data['time'], \
                    veh_data['vehicle_ID'], (veh_data['total_dist_traveled'] * self.FT_CONVERSION)))
            return True

        if veh_data['prev_tp_travel_SPOT'] is not None:
            if abs(Get_Heading_Change(veh_data['prev_SPOT_heading'], veh_data['heading'])) >= 45:
                if self.CF.Control['OutputLevel'] >= 2:
                    logger.debug('Travel SPOT generated at time: %s for vehicle ID: %s because heading change of: %s degrees' % (veh_data['time'], veh_data['vehicle_ID'],\
                        Get_Heading_Change(veh_data['prev_SPOT_heading'], veh_data['heading'])))
                return True

            elif (abs(veh_data['prev_SPOT_distance'] - veh_data['total_dist_traveled']) * self.FT_CONVERSION) >= 200: # convert feet to meters
                if self.CF.Control['OutputLevel'] >= 2:
                    logger.debug('Travel SPOT generated at time: %s for vehicle ID: %s because distance traveled of: %s meters' % (veh_data['time'], veh_data['vehicle_ID'], \
                        (abs(veh_data['prev_SPOT_distance'] - veh_data['total_dist_traveled']) * self.FT_CONVERSION)))
                return True

        return False


    #-------------------------------------------------------------------------
    def Generate(self, veh_data, SPOT_type, yawrate = None, accel = None):
        """
        Generate an ITS Spot message of the specified type for the current vehicle and add to the vehicle's ITS Spot buffer

        :param veh_data: The vehicle data of the vehicle transmitting the message
        :param SPOT_type: The type of ITS Spot (1 = Travel record, 2 = Behavior record)
        :param yawrate: The current yaw angular velocity of the vehicle
        :param accel: The current acceleration of the vehicle
        """

        if SPOT_type == 1:
            if veh_data['accel_instantaneous'] is not None:
                accel = veh_data['accel_instantaneous']
            else:
                accel = veh_data['average_acceleration']

            SPOT = {'localtime' : veh_data['time'],
                    'x' : veh_data['location_x'],
                    'y' : veh_data['location_y'],
                    'spd' : veh_data['speed'] * self.SPOT_SPD_CONVERSION,
                    'heading' : veh_data['heading'],
                    'yawrate' : veh_data['yawrate'],
                    'accel' : accel * self.ACCEL_CONVERSION,
                    'vehicle_ID' : veh_data['vehicle_ID'],
                    'dist_traveled' : veh_data['total_dist_traveled'],
                    }

            veh_data['prev_SPOT_distance'] = veh_data['total_dist_traveled']
            veh_data['prev_SPOT_heading'] = veh_data['heading']

        elif SPOT_type == 2: # SPOT Behavior Record (due to acceleration/yawrate)
            if accel is not None:
                SPOT = {'localtime' : veh_data['SPOT_accel_tp'],
                        'x' : veh_data['SPOT_accel_X'],
                        'y' : veh_data['SPOT_accel_Y'],
                        'spd' : veh_data['SPOT_accel_v'] * self.SPOT_SPD_CONVERSION,
                        'heading' : veh_data['SPOT_accel_heading'],
                        'yawrate' : veh_data['SPOT_accel_yawrate'],
                        'accel' : accel * self.ACCEL_CONVERSION,
                        'vehicle_ID' : veh_data['vehicle_ID'],
                        }
            elif yawrate is not None:
                SPOT = {'localtime' : veh_data['SPOT_yawrate_tp'],
                        'x' : veh_data['SPOT_yawrate_X'],
                        'y' : veh_data['SPOT_yawrate_Y'],
                        'spd' : veh_data['SPOT_yawrate_v'] * self.SPOT_SPD_CONVERSION,
                        'heading' : veh_data['SPOT_yawrate_heading'],
                        'yawrate' : yawrate,
                        'accel' : veh_data['SPOT_yawrate_accel'] * self.ACCEL_CONVERSION,
                        'vehicle_ID' : veh_data['vehicle_ID'],
                        }


        self.SPOTBuffer.AddSPOT(SPOT,SPOT_type)


    #-------------------------------------------------------------------------
    def CheckMessage(self, veh_data, tp):
        """
        Check to see if the current vehicle has triggered an ITS Spot message

        :param veh_data: The vehicle data of the vehicle transmitting the message
        :param tp: the current time period
        """

        # Check vehicle distance traveled and heading to determine if generating a Travel Record SPOT
        if (tp % 1.0 == 0) and self.CheckTravelRecords(veh_data):
            self.Generate(veh_data = veh_data, SPOT_type = 1)
            veh_data['prev_tp_travel_SPOT'] = tp

        # If sensing frequency is valid, check for Behavior Record SPOT
        if SPOT_time(tp, self.CF.Strategy['SPOTBehaviorSensingFrequency']):
            # Behavior Records: Check if acceleration greater than -0.25g or yaw rate > +-8.5 deg/s
            if veh_data['accel_instantaneous'] is not None:
                accel = veh_data['accel_instantaneous']
            else:
                accel = veh_data['average_acceleration']


            if accel <= self.SPOT_accel_threshold:
                # Check to see if this is the start of a new time period
                if veh_data['SPOT_accel_tp'] is None:
                    veh_data['SPOT_accel_tp'] = tp
                # Check to see if there is a new deceleration peak (current accel < recorded max)
                if accel < veh_data['max_SPOT_accel']:
                    veh_data['max_SPOT_accel'] = accel
                    veh_data['SPOT_accel_X'] = veh_data['location_x']
                    veh_data['SPOT_accel_Y'] = veh_data['location_y']
                    veh_data['SPOT_accel_v'] = veh_data['speed']
                    veh_data['SPOT_accel_heading'] = veh_data['heading']
                    veh_data['SPOT_accel_yawrate'] = veh_data['yawrate']

            # Else, check to see if a threshold period just finished
            else:
                if veh_data['SPOT_accel_tp'] is not None:
                    if self.CF.Control['OutputLevel'] >= 2:
                        logger.debug('Behavior SPOT generated at time: %s for vehicle ID: %s because deceleration of: %s g' % (veh_data['time'], veh_data['vehicle_ID'], \
                            (veh_data['max_SPOT_accel'] * self.ACCEL_CONVERSION)))
                    # Generate SPOT
                    self.Generate(veh_data = veh_data, SPOT_type = 2, accel = veh_data['max_SPOT_accel'])
                    veh_data['prev_tp_accel_SPOT'] = veh_data['SPOT_accel_tp']
                    # Reset max accel to zero
                    veh_data['max_SPOT_accel'] = 0.0
                    veh_data['SPOT_accel_tp'] = None
                    veh_data['SPOT_accel_X'] = 0.0
                    veh_data['SPOT_accel_Y'] = 0.0
                    veh_data['SPOT_accel_v'] = 0.0
                    veh_data['SPOT_accel_heading'] = 0.0
                    veh_data['SPOT_accel_yawrate'] = 0.0

            if veh_data['yawrate'] is not None and abs(veh_data['yawrate']) > self.SPOT_yawrate_threshold:
                # Check to see if this is the start of a new time period
                if veh_data['SPOT_yawrate_tp'] == None:
                    veh_data['SPOT_yawrate_tp'] = tp
                # Check to see if there is a new peak (current yaw rate > recorded max)
                if abs(veh_data['max_SPOT_yawrate']) < abs(veh_data['yawrate']):
                    veh_data['max_SPOT_yawrate'] = veh_data['yawrate']
                    veh_data['SPOT_yawrate_X'] = veh_data['location_x']
                    veh_data['SPOT_yawrate_Y'] = veh_data['location_y']
                    veh_data['SPOT_yawrate_v'] = veh_data['speed']
                    veh_data['SPOT_yawrate_heading'] = veh_data['heading']
                    veh_data['SPOT_yawrate_accel'] = accel

            # Else, check to see if a threshold period just finished (max yawrate > 0)
            else:
                if veh_data['SPOT_yawrate_tp'] is not None:
                    # Check to make sure an ITS Spot behavior record wasn't already taken for acceleration
                    if (veh_data['prev_tp_accel_SPOT'] is None) or (round(veh_data['SPOT_yawrate_tp']) != round(veh_data['prev_tp_accel_SPOT'])):
                        if self.CF.Control['OutputLevel'] >= 2:
                            logger.debug('Behavior SPOT generated at time: %s for vehicle ID: %s because yawrate of: %s deg/sec' % (veh_data['time'], veh_data['vehicle_ID'], \
                                veh_data['max_SPOT_yawrate']))
                        # Generate SPOT
                        self.Generate(veh_data = veh_data, SPOT_type = 2, yawrate = veh_data['max_SPOT_yawrate'])
                        veh_data['prev_tp_yawrate_SPOT'] = tp

                    elif self.CF.Control['OutputLevel'] >= 3:
                        logger.debug('Behavior SPOT not generated at time: %s for vehicle ID: %s due to yawrate because ITS Spot already taken for acceleration' %
                                (veh_data['time'], veh_data['vehicle_ID']))

                    # Reset max yaw rate to zero
                    # Reset max accel to zero
                    veh_data['max_SPOT_yawrate'] = 0.0
                    veh_data['SPOT_yawrate_tp'] = None
                    veh_data['SPOT_yawrate_X'] = 0.0
                    veh_data['SPOT_yawrate_Y'] = 0.0
                    veh_data['SPOT_yawrate_v'] = 0.0
                    veh_data['SPOT_yawrate_heading'] = 0.0
                    veh_data['SPOT_yawrate_accel'] = 0.0

#-------------------------------------------------------------------------
    def CheckRange(self, veh_data, tp):
        """
        Check for ITS Spot devices in range of the current vehicle
        :param veh_data: The current vehicle data
        :param tp: The current time period
        """

        Inrange_SPOTdevices = self.SPOT_tree.find_range(veh_data['location_x'], veh_data['location_y'])
        clear_SPOT_buffer = False

        for SPOT in Inrange_SPOTdevices:

            if veh_data['vehicle_ID'] in self.SPOTBuffer.ActiveBuffers.keys():
                travelSPOTs, behaviorSPOTs = self.SPOTBuffer.TransmitSPOTBuffer(veh_data)
                if (len(travelSPOTs)+len(behaviorSPOTs)) > 0:
                    self.Travelmsgs.extend(travelSPOTs)
                    self.BehaviorMsgs.extend(behaviorSPOTs)
                    clear_SPOT_buffer = True
                    veh_data['SPOT_trans_tp'] = tp
                    if self.CF.Control["OutputLevel"] >= 2:
                        logger.debug("%s ITS Spot messages transmitted at time %d from vehicle ID: %s" % \
                            ((len(travelSPOTs)+len(behaviorSPOTs)), veh_data["time"], veh_data['vehicle_ID']))

        if clear_SPOT_buffer:
            self.SPOTBuffer.ClearBuffer(veh_data['vehicle_ID'])

#-------------------------------------------------------------------------

    def Write(self, clear_all=False):

        if (len(self.BehaviorMsgs) >= self.msg_limit) or clear_all:
            if len(self.BehaviorMsgs) > 0:
                df = pd.DataFrame(self.BehaviorMsgs)
                df['spd'] = df['spd'].map(lambda x: '%.2f' % x)
                df['yawrate'] = df['yawrate'].map(lambda x: '%.1f' % x)
                df['heading'] = df['heading'].map(lambda x: '%.1f' % x)
                df['accel'] = df['accel'].map(lambda x: '%.2f' % x)

                #reorder data elements
                df = df[self.Behavior_col_order]

                df.rename(columns={
                 'vehicle_ID': 'Vehicle_ID',
                 'localtime': 'Time_Taken',
                 'accel': 'Acceleration',
                 'heading': 'Heading',
                 'spd': 'Speed',
                 'x': 'X',
                 'y': 'Y',
                 'yawrate': 'YawRate'
                 }, inplace=True)

                df.to_csv(path_or_buf = self.CF.Control['SPOTBehaviorFile'],
                               index=False,
                               mode='a',
                               header = self.header,
                                )
            if len(self.Travelmsgs) > 0:
                df = pd.DataFrame(self.Travelmsgs)
                df['spd'] = df['spd'].map(lambda x: '%.2f' % x)

                #reorder data elements
                df = df[self.Travel_col_order]

                df.rename(columns={
                 'vehicle_ID': 'Vehicle_ID',
                 'localtime': 'Time_Taken',
                 'spd': 'Speed',
                 'x': 'X',
                 'y': 'Y',
                 }, inplace=True)

                df.to_csv(path_or_buf = self.CF.Control['SPOTTravelFile'],
                               index=False,
                               mode='a',
                               header = self.header,
                                )

                self.header = False
