#external
import pandas as pd

#TCA
from TCACore import Timer, logger
from TCARandom import Random_generator

class BSM(object):

    def __init__(self, RandomGen_seed, CF, regions, msg_limit = 800000):
        """
        Initializes a BSM module

        :param RandomGen_seed: The random seed
        """
        self.random_generator = Random_generator(RandomGen_seed)
        self.CF = CF
        self.regions = regions

        self.random_generator.add_generator_bit('BSM_Tmp_ID', 32)
        self.random_generator.add_generator_int('LossPercent', 1, 100)

        #Limit of message list before printing to a file
        self.msg_limit = msg_limit

        self.BSM_list = []
        self.headerBSM = True

        self.BSM_col_order = ['DSRC_MessageID',
                            'Vehicle_ID',
                            'BSM_tmp_ID',
                            'transtime',
                            'x',
                            'y',
                            'spd',
                            'accel',
                            'heading',
                            'brakeStatus',
                            'brakePressure',
                            'hardBraking',
                            'transTo',
                            'transmission_received_time',]

        if self.regions is not None:
            for Event in self.regions.Event_titles:
                 self.BSM_col_order.append(Event)


#-------------------------------------------------------------------------

    def CheckBrakes(self, veh_data):
        """
        Checks brake status of given vehicle using instantaneous acceleration

        :param veh_data: Vehicle whose brakes to check
        """

        # Set brake_status as applied if decelerating more than the defined threshold
        veh_data['brake_status'] = '0000'
        if veh_data['average_acceleration'] <= self.CF.Strategy['BrakeThreshold'] \
                and veh_data['average_acceleration'] is not None:
                    veh_data['brake_status'] = '1111'

        # Only set the brake pressure if instantaneous acceleration is available
        if veh_data['accel_instantaneous'] != None:

            if veh_data['accel_instantaneous'] <= 0:
                veh_data['brake_pressure'] =  veh_data['accel_instantaneous']
            else:
                veh_data['brake_pressure'] = 0.0


        # Set the hard braking (1: true, 0: false) if decelerating greater than 0.4g (J2735 standard) or approx. 12.9 ft/s^2
        veh_data['hard_braking'] = 0
        if veh_data['average_acceleration'] <= -12.869619 \
            and veh_data['average_acceleration'] is not None:
                veh_data['hard_braking'] = 1


#-------------------------------------------------------------------------
    def GenerateTransmit(self, veh_data, transTo, latency=0, isCellular=False, isRSE=False):
        """
        Creates BSM message and adds it to the BSM list

        :param veh_data: The vehicle data of the vehicle transmitting the message
        :param transTo: The RSE or Cellular Region being transmitted to
        :param latency: The latency between sending and receiving the message, default is 0
        :param isCellular: True if the vehicle is sending the message by Cellular, default is False
        :param isRSE: True if the vehicle is sending the message by RSE, default is False
        """

        if veh_data['BSM_equipped']:
            transmitted = True

            #Check if vehicle is within a defined cellular region
            if self.regions is not None and isCellular:
                if len(self.regions.cell_regions) > 0:
                    for region in self.regions.cell_regions:
                        if region.in_region(veh_data['location_x'], veh_data['location_y']):
                            #Assign the defined regions loss percentage and latency
                            latency = float(region.latency)
                            if self.random_generator['LossPercent'] < float(region.loss):
                                transmitted = False
                            transTo = region.title

            if transmitted:
                BSM = {
                    'Vehicle_ID' : veh_data['vehicle_ID'],
                    'BSM_tmp_ID' : veh_data['BSM_tmp_ID'],
                    'localtime' : veh_data['time'],
                    'spd' : veh_data['speed'],
                    'x' : veh_data['location_x'],
                    'y' : veh_data['location_y'],
                    'transtime' : veh_data['time'],
                    'transTo' : transTo,
                    'avg_accel' : veh_data['average_acceleration'],
                    'brakeStatus' : veh_data["brake_status"],
                    'brakePressure' : veh_data['brake_pressure'],
                    'hardBraking' : veh_data['hard_braking'],
                    'transmission_received_time' : veh_data['time'] + latency,
                    'heading' : veh_data['heading'],
                }
                if veh_data['accel_instantaneous'] != None:
                    BSM["instant_accel"] = veh_data['accel_instantaneous']

                # if veh_data['link'] is not None:
                #     BSM['link'] = veh_data['link']

                if self.regions is not None:
                    for region_name in self.regions.Event_titles:
                        BSM[region_name] = veh_data[region_name]

                #Add BSM to the Main BSM list
                self.BSM_list.append(BSM)


#-------------------------------------------------------------------------
    def tmp_ID_check(self, veh_data, tp):
        """
        Checks if the BSM ID needs to be updated

        :param veh_data:  The vehicle to check
        :param tp: The time period in seconds to check
        :return:
        """

        if tp >=veh_data['BSM_time_to_ID_chg'] :
            veh_data['BSM_tmp_ID'] = self.random_generator['BSM_Tmp_ID']
            #TODO updated change time to user defined with default of 300 secs
            veh_data['BSM_time_to_ID_chg'] = tp + 300.0


#-------------------------------------------------------------------------

    def Write(self, clear_buffer=False):

        if (len(self.BSM_list) >= self.msg_limit) or clear_buffer:
            df = pd.DataFrame(self.BSM_list)
            df = df.sort(['transtime', 'Vehicle_ID'])
            df['avg_accel'] = df['avg_accel'].fillna(-9999.0)
            df['heading'] = df['heading'].fillna(-9999.0)
            df['spd'] = df['spd'].map(lambda x: '%.3f' % x)
            df['heading'] = df['heading'].map(lambda x: '%.1f' % x)
            df['DSRC_MessageID'] = '{0:0>2}'.format(2)

            # Use instantaneous acceleration if available from input data, otherwise use average acceleration
            if 'instant_accel' in df.columns:
                df.rename(columns={'instant_accel': 'accel'}, inplace=True)
                accel_col_name = 'Instant_Acceleration'
            else:
                df.rename(columns={'avg_accel': 'accel'}, inplace=True)
                accel_col_name = 'Avg_Acceleration'

            df['accel'] = df['accel'].map(lambda x: '%.3f' % x)
            #reorder data elements
            df = df[self.BSM_col_order]

            df.rename(columns={
             'vehicle_ID': 'Vehicle_ID',
             'localtime': 'Time_Taken',
             'accel' : accel_col_name,
             'heading': 'Heading',
             'spd': 'Speed',
             'x': 'X',
             'y': 'Y',
             'yawrate': 'YawRate'
             }, inplace=True)

            df.to_csv(path_or_buf = self.CF.Control["BSMTransFile"],
                           index=False,
                           mode='a',
                           header = self.headerBSM,
                            )
            self.headerBSM = False
            self.BSM_list = []