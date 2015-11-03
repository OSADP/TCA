#external
import pandas as pd

#TCA
from TCABuffer import CLBuffer
from TCACore import Timer, logger
from TCARandom import Random_generator

class PDM(object):

    def __init__(self, RandomGen_seed, CF, RSE_tree, regions, msg_limit = 800000):

        """
        Initializes a PDM module

        :param RandomGen_seed: The random seed
        """
        self.random_generator = Random_generator(RandomGen_seed)
        self.CF = CF
        self.regions = regions

        self.random_generator.add_generator_int('psn', 0, 32767)  #range based on J2735
        self.random_generator.add_generator_int('GapDistance', CF.Strategy["GapMinDistance"], CF.Strategy["GapMaxDistance"])
        self.random_generator.add_generator_int('GapTimeout', CF.Strategy["GapMinTime"], CF.Strategy["GapMaxTime"])

        #Buffer Manager for PDM Snapshots
        self.PDMBuffer = CLBuffer(CF.Strategy['TotalCapacity'])
        self.PDM_list = []

        #Limit of message list before printing to a file
        self.msg_limit = msg_limit
        self.headerPDM = True

        self.PDM_col_order =["DSRC_MessageID",
                             "x",
                             "y",
                             "localtime",
                             "num",
                             "VID",
                             "PSN",
                             "ss_num",
                             "msg_num",
                             "spd",
                             "accel",
                             "lastRSE",
                             "type",
                             "transtime",
                             "transTo",
                             'deltime',
                             'delreason',
                             'transmission_received_time',
                             'link',
                             'yawrate',]

        if self.regions is not None:
            for Event in self.regions.Event_titles:
                 self.PDM_col_order.append(Event)


    #-------------------------------------------------------------------------

    def PSNCheck(self, veh_data, tp):
        """
        If the given vehicle has transmitted a message in the given time, changes PSN or activates privacy gap
        If privacy gaps are enabled, checks to see if the given vehicle has expired PSN and enters privacy gap if so
        If the given vehicle is in a privacy gap, checks to see if the gap has expired and if so vehicle is given new PSN

        :param veh_data: The vehicle to check
        :param tp: The time period in seconds to check
        """

        def change_PSN(veh_data, tp):
            """
            Sets the given vehicle's PSN to a new random value and resets PSN change triggers

            :param veh_data: The vehicle whose PSN is changed
            :param tp: The time period that the change occurrs in
            """
            veh_data['PSN'] = self.random_generator['psn']
            veh_data['PSN_distance_to_change'] = veh_data['total_dist_traveled']  + self.CF.Strategy["DistanceBetweenPSNSwitches"]
            veh_data['PSN_time_to_end_of_PSN'] = tp + self.CF.Strategy['TimeBetweenPSNSwitches']
            if self.CF.Control["OutputLevel"] >= 2:
                logger.debug("PSN changed to %d for vehicle ID %s at time %s because of RSE transmission"
                             % (veh_data['PSN'],  veh_data['vehicle_ID'], tp))

        def start_gap( veh_data, tp):
                """
                Starts a new privacy gap for the given vehicle

                :param veh_data: The vehicle entering the privacy gap
                :param tp: The time period that the privacy gap starts in
                """
                veh_data['PSN'] = -1
                veh_data['PSN_time_to_end_gap'] = tp +  self.random_generator['GapTimeout']
                veh_data['PSN_distance_to_end_of_gap'] =  veh_data['total_dist_traveled'] + self.random_generator['GapDistance']
                if self.CF.Control["OutputLevel"] >= 2:
                    logger.debug("Vehicle ID %s at time %s enters PSN privacy gap because of RSE transmission"
                                 % (veh_data['vehicle_ID'], tp))
                veh_data['privacy_gap_start'] = tp
                veh_data['in_privacy_gap'] = True

        #Change PSN or activate privacy gap if vehicle has transmitted to an RSE and is PDM equipped
        if veh_data['dsrc_transmit_pdm']  and (veh_data['prev_time_PDM_dsrc_transmit'] == tp):
            if self.CF.Strategy["GapMaxDistance"] == 0 or self.CF.Strategy["GapMaxTime"] == 0:
                change_PSN(veh_data, tp)
            else:
                start_gap(veh_data, tp)



        #4.1 check whether the distance and time has expired of current PSN if not in gap
        if (veh_data['in_privacy_gap'] == False) \
            and (tp >= veh_data['PSN_time_to_end_of_PSN']) \
            and (veh_data['total_dist_traveled'] >= veh_data['PSN_distance_to_change']):


            #4.4 Check for Gap  (Note if CF.Strategy["Gap"]=0 then no Gaps are added)
            if self.CF.Strategy["Gap"] == 1:
                start_gap(veh_data, tp)
            else:
                change_PSN(veh_data, tp)


        #4.5 Check to see if privacy gap has expired; generate new PSN
        if veh_data['in_privacy_gap'] and \
           (veh_data['total_dist_traveled'] >= veh_data['PSN_distance_to_end_of_gap']) or \
           (tp >= veh_data['PSN_time_to_end_gap']):

                change_PSN(veh_data, tp )
                veh_data['in_privacy_gap'] = False
                if self.CF.Control["OutputLevel"] >= 2:
                    logger.debug("PSN changed to %d for vehicle ID %s at time %s because privacy gap expired" %
                                     (veh_data['PSN'], veh_data['vehicle_ID'], tp))

    # Check Snapshot Trigger
    #-------------------------------------------------------------------------
    def CheckMessage(self, veh, tp):

        """
        Checks the defined PDM snapshot triggers for the given vehicle in the given time to see if a
        PDM should be generated

        :param veh: The vehicle to check
        :param tp:  The time period to check in
        """
        PDM_generated = False

        #Only vehicles that have been active in the network for the user-defined amount of time or distance
        #The default J2735 values are: 500m or 120 seconds
        if (veh['total_dist_traveled'] >= self.CF.Strategy['DistanceBeforePDMCollection']) or \
           (veh['total_time_in_network'] >= self.CF.Strategy['TimeBeforePDMCollection']):

                #2.1 Stop Trigger
                #2.1.1

                if veh['speed'] > 0:
                    veh['time_motionless'] = 0
                else:
                    veh['time_motionless'] += 1

                #Query all vehicles whose Motionless value is greater than Stop Threshold that haven't taken a Stop SS
                #since the StopLag time and mark that a stop snapshot was taken and update the time since last stop and distance
                #since last stop.
                if ((veh['time_motionless'] > self.CF.Strategy['StopThreshold']) and \
                    (veh['looking_for_start'] == False)):

                    veh['looking_for_start'] = True
                    veh['time_of_last_stop'] = tp

                    self.Generate(veh_data = veh, type = 1, time = tp)
                    PDM_generated = True


                #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                #2.2 Start Trigger
                #2.2.1
                #Query all vehicles that currently have their looking for a start value set to true and whose speed
                #is greater than Start Threshold and mark that a start snapshot was taken and revert looking for a
                #start to false

                if (veh['looking_for_start'])  and (veh['speed'] >= self.CF.Strategy['StartThreshold']):

                    veh['looking_for_start'] = False
                    veh['time_of_start_snapshot'] = tp

                    self.Generate(veh_data = veh, type = 2, time = tp)
                    PDM_generated = True


                #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                #2.3 Periodic Trigger
                #2.3.1 and #2.3.2 (speed exception)
                #Query all vehicles that have not taken a start or stop snapshot, do not have their looking for
                #a start value set for true and whose time until their next periodic snapshot is <= the current time
                #and mark that a periodic snapshot was taken and re-calculate the time until the next periodic.

                if (veh['looking_for_start'] == False) and (veh['time_to_next_periodic'] <= tp) and \
                        (PDM_generated == False):

                    veh['time_of_periodic_snapshot'] = tp

                    self.Generate(veh_data = veh, type = 3, time = tp)

                    if self.CF.Control["OutputLevel"] >= 2:
                        logger.debug('Periodic SS Created for Vehicle ID %s at time:%s' % (veh['vehicle_ID'], tp))

                    #check for when the next check should be
                    if veh['speed'] <= self.CF.Strategy["LowSpeedThreshold"]:
                        IncreaseTime = self.CF.Strategy["ShortSpeedInterval"]
                    elif veh['speed'] >= self.CF.Strategy["HighSpeedThreshold"]:
                        IncreaseTime = self.CF.Strategy["LongSpeedInterval"]
                    else:         #Speed Interpolation
                        slope = (veh['speed'] - self.CF.Strategy["LowSpeedThreshold"]) / \
                                (self.CF.Strategy["HighSpeedThreshold"] - self.CF.Strategy["LowSpeedThreshold"])
                        IncreaseTime = round(self.CF.Strategy["ShortSpeedInterval"] + slope *
                                             (self.CF.Strategy["LongSpeedInterval"] - self.CF.Strategy["ShortSpeedInterval"]))

                    #increase time counter
                    veh['time_to_next_periodic'] = tp + IncreaseTime


    #-------------------------------------------------------------------------
    def Generate(self, veh_data, type, time):

        """
        Creates a PDM and adds it to the PDM list

        :param veh_data: The vehicle to create a PDM for
        :param type: The vehicle type creating the PDM
        :param time: The time the PDM is being created
        """

        if self.CF.Control["OutputLevel"] >= 3:
            logger.debug("PDM type %d created in vehicle %s" % (type, veh_data['vehicle_ID']))


        #9.0 Update Snapshot log

        if veh_data['vehicle_ID'] in self.PDMBuffer.ActiveBuffers.keys():
            lastRSE = self.PDMBuffer.GetLastRSE(veh_data['vehicle_ID'])
        else:
            lastRSE = 0

        #Add Snap Shot to Main SS List
        SS = {
            'VID' : veh_data['vehicle_ID'],
            'num' : len(self.PDM_list) + 1,
            'time' :  time,
            'localtime' :  time,
            'PSN' : veh_data['PSN'],
            'spd' : veh_data['speed'],
             'x' : veh_data['location_x'],
             'y' : veh_data['location_y'],
             'type' : type,
             'lastRSE' : lastRSE,
             'transtime' : -1,
             'transTo' : -1,
             'deltime' : 0,
             'delreason' : 0,
             'transmission_received_time' : -1,
             'link' : veh_data['link'],
             'yawrate': veh_data['yawrate'],
        }

        # Add acceleration to the PDM Snapshot
        if veh_data['accel_instantaneous'] is not None:
            SS['instant_accel'] = veh_data['accel_instantaneous']
        else:
            SS['avg_accel'] = veh_data['average_acceleration']

        # Add any event values to the PDM Snapshot
        if self.regions is not None:
            for Event in self.regions.Event_titles:
                SS[Event] = veh_data[Event]

        self.PDM_list.append(SS)


        #9.1 Manage Vehicle Buffer Contents
        if (veh_data["in_privacy_gap"] != True) and (SS["PSN"] != -1):
            self.PDMBuffer.AddSS(veh_data = veh_data,
                                SS = SS,
                                locT = time,
                                Snapshots = self.PDM_list,
                                CF = self.CF)
        else:
            self.PDMBuffer.DeleteSSinLog(SS = SS, locT = time, reason = 3, Snapshots = self.PDM_list)


#-------------------------------------------------------------------------

    def Write(self, clear_buffer = False, LastTP = None):

        if clear_buffer:
            for ID in self.PDMBuffer.ActiveBuffers.keys():
                self.PDMBuffer.ClearBuffer(vehicleID = ID, locT = LastTP + 2, Snapshots = self.PDM_list,
                                            reason = 2, transmitted_to = -1, transTime = -1)

        if (len(self.PDM_list) >= self.msg_limit) or clear_buffer:
            df = pd.DataFrame(self.PDM_list)
            df = df.sort(['localtime', 'num', 'VID'])

            df['spd'] = df['spd'].map(lambda x: '%.3f' % x)
            df['DSRC_MessageID'] = '{0:0>2}'.format(9)

            # Use instantaneous acceleration if available from input data, otherwise use average acceleration
            if 'instant_accel' in df.columns:
                df.rename(columns={'instant_accel': 'accel'}, inplace=True)
                accel_col_name = 'Instant_Acceleration'
            else:
                df['avg_accel'] = df['avg_accel'].fillna(-9999.000)
                df.rename(columns={'avg_accel': 'accel'}, inplace=True)
                accel_col_name = 'Avg_Acceleration'

            df['accel'] = df['accel'].map(lambda x: '%.3f' % x)

            #reorder data elements
            df = df[self.PDM_col_order]

            df.rename(columns={
                 'VID': 'Vehicle_ID',
                 'localtime': 'Time_Taken',
                 'spd': 'Speed',
                 'accel': accel_col_name,
                 'x': 'Location_X',
                 'y': 'Location_Y',
                 'lastRSE': 'Last_RSE',
                 'type': 'Msg_Type',
                 'transtime': 'Transmit_Time',
                 'transTo': 'Transmit_To',
                 'deltime': 'Delete_Time',
                 'delreason': 'Delete_Reason',
                 'num': 'SS_count',
                 'ss_num': 'Vehicle_SS_Number',
                 'msg_num': 'Message_SS_Number',
                 'transmission_received_time' : 'Received_Time',
                 }, inplace=True)

            PDM_all_col = ['DSRC_MessageID',
                             'Vehicle_ID',
                             'Time_Taken',
                             'PSN',
                             'Speed',
                             accel_col_name,
                             'Location_X',
                             'Location_Y',
                             'yawrate',
                             'Msg_Type',
                             'Transmit_To',
                             'Transmit_Time',
                             'Received_Time',
                             'Message_SS_Number',
                             'Vehicle_SS_Number',
                             'SS_count',
                             'Delete_Time',
                             'Delete_Reason']
            if self.regions is not None:
                for Event in self.regions.Event_titles:
                    PDM_all_col.append(Event)
            
            df.to_csv(path_or_buf = self.CF.Control["PDMAllFile"],
                           index=False,
                           mode='a',
                           header = self.headerPDM,
                           cols=PDM_all_col)

            #Remove non-transmitted messages
            df = df[(df["Delete_Reason"] == 0) & (df["Transmit_Time"] != 0)]


            PDM_trans_col = ['DSRC_MessageID',
                             'Time_Taken',
                             'PSN',
                             'Speed',
                             accel_col_name,
                             'Location_X',
                             'Location_Y',
                             'yawrate',
                             'Msg_Type',
                             'Transmit_To',
                             'Transmit_Time',
                             'Received_Time',
                             'Message_SS_Number',
                             'Vehicle_SS_Number',]
            if self.regions is not None:
                for Event in self.regions.Event_titles:
                    PDM_trans_col.append(Event)

            df.to_csv(path_or_buf = self.CF.Control["PDMTransFile"],
                           index=False,
                           mode='a',
                           header = self.headerPDM,
                           cols=PDM_trans_col)


            self.headerPDM = False
            self.PDM_list = []