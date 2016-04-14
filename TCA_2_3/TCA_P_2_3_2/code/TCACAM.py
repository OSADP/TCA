#external
import pandas as pd

#TCA
from TCACore import Timer, logger
from TCARandom import Random_generator

class CAM(object):

    def __init__(self, RandomGen_seed, CF, msg_limit = 800000):
        """
        Initializes a CAM module

        :param RandomGen_seed: The random seed
        """
        self.random_generator = Random_generator(RandomGen_seed)
        self.CF = CF

        #Limit of message list before printing to a file
        self.msg_limit = msg_limit

        self.CAM_list = []
        self.headerCAM = True

        self.random_generator.add_generator_int('Station_ID', 1, 4294967295) #based ITS-S standard


#-------------------------------------------------------------------------

    def CheckMessage(self, veh, tp):
        """
        Checks CAM snapshot triggers to see of a CAM should be generated

        :param veh: Vehicle to check for CAM for
        :param tp: Time period to check for CAM in
        :return: True if CAM should be generated
        """

        #Distance Change: The current position and position included in previous CAM exceeds 4 m (13.1234 feet)
        if veh['total_dist_traveled'] > veh['last_CAM_distance'] + 13.1234:
            return True

        #Speed Change: The absolute difference between current speed and speed included in previous CAM exceeds 0.5 m/s (1.11847 mph)
        if (veh['last_CAM_heading'] is None) or \
           (veh['speed'] > veh['last_CAM_speed'] + 1.11847) or \
           (veh['speed'] <= veh['last_CAM_speed'] - 1.11847):
                 return True

        #Heading Change: The absolute difference between current direction of the originating ITS-S (towards North) and direction included in previous CAM exceeds 4 degrees;
        if veh['heading'] is not None:
            if veh['last_CAM_heading'] is None or (abs(((veh['last_CAM_heading'] - veh['heading'] + 180) % 360) - 180) > 4):
                return True

        #Max time Change
        if tp - veh['last_CAM_time'] >= 1.0:
            return True

#-------------------------------------------------------------------------
    def GenerateTransmit(self, veh_data, transTo, tp):
        """
        Creates CAM message and adds it to the CAM list

        :param veh_data: Vehicle that is generating the message
        :param transTo: RSE that the message is transmitted to
        :param tp: The time the message is being generated
        """

        if veh_data['CAM_equipped']:
            # Hard coded values are set to CAM defaults
            CAM = {
                'Vehicle_ID' : veh_data['vehicle_ID'],
                'protocolVersion' : 1,
                'messageID' : 2,
                'stationID' : veh_data['CAM_Station_ID'],
                'generationDeltaTime' : veh_data['time'] * 1000, # Convert seconds to milliseconds
                'stationType' : 5,
                'latitude' : veh_data['location_x'],
                'longitude' : veh_data['location_y'],
                'semiMajorConfidence' : 4095,
                'semiMinorConfidence' : 4095,
                'altitudeValue' : 800001,
                'heading' : veh_data['heading'],
                'headingConfidence' : 127,
                'speed' : (veh_data['speed'] * 0.44704), # Convert mph to m/s
                'speedConfidence' : 127,
                'driveDirection' : 2,
                'curvatureValue' : 30001,
                'curvatureConfidence' : 7,
                'yawRateValue' : veh_data['yawrate'],
                'yawRateConfidence' : 8,
                'vehicleLengthValue' : 1023,
                'vehicleLengthConfidence' : 3,
                'vehicleWidth' : 62
            }
            if veh_data['accel_instantaneous'] != None:
                CAM['longitudinalAcceleration'] = veh_data['accel_instantaneous'] * 0.3048 # Convert f/s2 to m/s2
            else:
                CAM['longitudinalAcceleration'] = 161

            #Add CAM to the Main CAM list
            self.CAM_list.append(CAM)

            veh_data['last_CAM_distance'] = veh_data['total_dist_traveled']
            veh_data['last_CAM_speed'] = veh_data['speed']
            veh_data['last_CAM_heading'] = veh_data['heading']
            veh_data['last_CAM_time'] = tp


#-------------------------------------------------------------------------

    def Write(self, clear_all=False):

        if (len(self.CAM_list) >= self.msg_limit) or clear_all:
            col = ['Vehicle_ID','protocolVersion','messageID','stationID','generationDeltaTime','stationType','latitude',
                   'longitude','semiMajorConfidence','semiMinorConfidence','altitudeValue','heading','headingConfidence',
                   'speed','speedConfidence','driveDirection','longitudinalAcceleration','curvatureValue','curvatureConfidence',
                   'yawRateValue','yawRateConfidence','vehicleLengthValue','vehicleLengthConfidence','vehicleWidth']

            df_CAMs = pd.DataFrame(self.CAM_list, columns=col)
            df_CAMs['speed'] = df_CAMs['speed'].map(lambda x: '%.3f' % x)
            df_CAMs['yawRateValue'] = df_CAMs['yawRateValue'].fillna(32767)
            df_CAMs['heading'] = df_CAMs['heading'].fillna(360)

            df_CAMs = df_CAMs.sort(['generationDeltaTime'])
            df_CAMs.to_csv(path_or_buf = self.CF.Control["CAMTransFile"], index = False,  mode = 'a', header = self.headerCAM)
            self.headerCAM = False
            self.CAM_list = []
