#Standard
import unittest

#TCA
from TCABuffer import CLBuffer, SPOTBuffer
from TCACore import  logger, Timer, Get_Heading_Change, SPOT_time
from TCADataStore import DataStorage


class TCA_Algorithm:
    def __init__(self, CF, RSEs, RSE_tree, RandomGen, Regions, SPOT_tree, BSM_limit = 800000, CAM_limit = 800000):

        """
        Initializes TCA_Algorithm module

        :param CF: Dictionary of Control File defined attributes
        :param RSEs: List of RSEs
        :param RSE_tree: Location tree of RSEs
        :param RandomGen: Seed value for randomization
        :param Regions: Regions class
        :param SPOT_tree: Location tree of SPOT devices
        :param BSM_limit: Limit of BSM list before outputting to a file
        :param CAM_limit: Limit of CAM list before outputting to a file
        """


        self.RSEs = RSEs
        self.RSE_tree = RSE_tree
        self.CF = CF
        self.randomgen = RandomGen
        self.regions = Regions
        self.SPOT_tree = SPOT_tree

        self.tbl = DataStorage(RandomGen)

        #Each Vehicle RSE list
        self.VehicleRSE = {}

        #Buffer Manager for PDM Snapshots
        self.PDMBuffer = CLBuffer(CF.Strategy['TotalCapacity'])
        self.SPOTBuffer = SPOTBuffer()

        #Master Snapshot Classes for hold all SS
        self.PDMs = []
        self.BSMs = []
        self.CAMs = []
        self.TravelSPOTmsgs = []
        self.BehaviorSPOTmsgs = []

        #Limit of BSM list before printing to a file
        self.BSM_limit = BSM_limit
        self.CAM_limit = CAM_limit

        self.FT_CONVERSION = 12 * 2.54 / 100 # converts feet to meters
        self.ACCEL_CONVERSION = 1 / 32.1740485564 # converts ft/s2 to g
        self.SPOT_SPD_CONVERSION = 1.609344 # converts mph to km/hr for ITS Spot Output
        self.SPOT_accel_threshold = CF.Strategy['SPOTaccelThreshold'] * 32.1740485564 # Convert g to ft/s^2 for ITS Spot Output
        self.SPOT_yawrate_threshold = CF.Strategy['SPOTyawrateThreshold'] * 32.1740485564 # Convert g to ft/s^2 for ITS Spot Output


    def pull_veh_data(self, veh, tp):
        """
        Returns vehicle data for specified time period.

        :param veh: The vehicle id for information to be retrieved
        :param tp: The time in seconds for information to be retrieved
        :return: The vehicle record for the vehicle at the specified time
        """
        return self.tbl.pull_veh_data(veh = veh, CF = self.CF, RandomGen = self.randomgen, Regions = self.regions, tp = tp)

    #-------------------------------------------------------------------------
    def CheckSPOTTravelRecords(self, veh_data):
        """
        Checks to see if the vehicle has triggered any of the requirements for producing an ITS Spot travel record

        :param veh_data: The vehicle data of the vehicle transmitting the message
        :return: True if the vehicle triggers an ITS Spot Travel Record, false otherwise
        """


        # Travel Records: Check that vehicle has traveled 200m since the beginning or since the last ITS Spot or changed heading by 45 degrees

        if veh_data['prev_tp_travel_SPOT'] is None and (veh_data['total_dist_traveled'] * self.FT_CONVERSION) >= 200: #convert feet to meters
            if self.CF.Control['OutputLevel'] >= 2:
                logger.debug('SPOT generated at time: %s for vehicle ID: %s because initial distance traveled of: %s meters' % (veh_data['time'], \
                    veh_data['vehicle_ID'], (veh_data['total_dist_traveled'] * self.FT_CONVERSION)))
            return True

        if veh_data['prev_tp_travel_SPOT'] is not None:
            if abs(Get_Heading_Change(veh_data['prev_SPOT_heading'], veh_data['heading'])) >= 45:
                if self.CF.Control['OutputLevel'] >= 2:
                    logger.debug('SPOT generated at time: %s for vehicle ID: %s because heading change of: %s degrees' % (veh_data['time'], veh_data['vehicle_ID'],\
                        Get_Heading_Change(veh_data['prev_SPOT_heading'], veh_data['heading'])))
                return True

            elif (abs(veh_data['prev_SPOT_distance'] - veh_data['total_dist_traveled']) * self.FT_CONVERSION) >= 200: # convert feet to meters
                if self.CF.Control['OutputLevel'] >= 2:
                    logger.debug('SPOT generated at time: %s for vehicle ID: %s because distance traveled of: %s meters' % (veh_data['time'], veh_data['vehicle_ID'], \
                        (abs(veh_data['prev_SPOT_distance'] - veh_data['total_dist_traveled']) * self.FT_CONVERSION)))
                return True

        return False


    #-------------------------------------------------------------------------
    def GenerateSPOT(self, veh_data, SPOT_type, yawrate = None, accel = None):
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
    def CheckSPOT(self, veh_data, tp):
        """
        Check to see if the current vehicle has triggered an ITS Spot message

        :param veh_data: The vehicle data of the vehicle transmitting the message
        :param tp: the current time period
        """

        # Check vehicle distance traveled and heading to determine if generating a Travel Record SPOT
        if (tp % 1.0 == 0) and self.CheckSPOTTravelRecords(veh_data):
            self.GenerateSPOT(veh_data = veh_data, SPOT_type = 1)
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
                        logger.debug('SPOT generated at time: %s for vehicle ID: %s because deceleration of: %s g' % (veh_data['time'], veh_data['vehicle_ID'], \
                            (veh_data['max_SPOT_accel'] * self.ACCEL_CONVERSION)))
                    # Generate SPOT
                    self.GenerateSPOT(veh_data = veh_data, SPOT_type = 2, accel = veh_data['max_SPOT_accel'])
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
                            logger.debug('SPOT generated at time: %s for vehicle ID: %s because yawrate of: %s deg/sec' % (veh_data['time'], veh_data['vehicle_ID'], \
                                veh_data['max_SPOT_yawrate']))
                        # Generate SPOT
                        self.GenerateSPOT(veh_data = veh_data, SPOT_type = 2, yawrate = veh_data['max_SPOT_yawrate'])
                        veh_data['prev_tp_yawrate_SPOT'] = tp
                        
                    elif self.CF.Control['OutputLevel'] >= 3:
                        logger.debug('SPOT not generated at time: %s for vehicle ID: %s due to yawrate because ITS Spot already taken for acceleration' % 
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
    def GenerateTransmitBSM(self, veh_data, transTo, latency=0, isCellular=False, isRSE=False):
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
                            if self.randomgen['LossPercent'] < float(region.loss):
                                transmitted = False
                            transTo = region.title

            if transmitted:
                BSM = {
                    'Vehicle_ID' : veh_data['vehicle_ID'],
                    'PSN' : veh_data['PSN'],
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

                if self.regions is not None:
                    for region_name in self.regions.Event_titles:
                        BSM[region_name] = veh_data[region_name]

                #Add BSM to the Main BSM list
                self.BSMs.append(BSM)


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
            veh_data['PSN'] = self.randomgen['psn']
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
                veh_data['PSN_time_to_end_gap'] = tp +  self.randomgen['GapTimeout']
                veh_data['PSN_distance_to_end_of_gap'] =  veh_data['total_dist_traveled'] + self.randomgen['GapDistance']
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
           (veh_data['total_dist_traveled'] >= veh_data['PSN_distance_to_end_of_gap']) and \
           (tp >= veh_data['PSN_time_to_end_gap']):

                change_PSN(veh_data, tp )
                veh_data['in_privacy_gap'] = False
                if self.CF.Control["OutputLevel"] >= 2:
                    logger.debug("PSN changed to %d for vehicle ID %s at time %s because privacy gap expired" %
                                     (veh_data['PSN'], veh_data['vehicle_ID'], tp))

    #2.0 Check Snapshot Trigger
    #-------------------------------------------------------------------------
    def CheckPDMSnapshot(self, veh, tp):

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

                #Query all vehicles whose time since last stop recorded is greater than Stop Lag,
                #whose Motionless value is greater than Stop Threshold and whose not looking
                #for a start and mark that a stop snapshot was taken and update the time since last stop and distance
                #since last stop.
                if (tp - veh['time_of_last_stop'] >= self.CF.Strategy['StopLag']) and \
                    (veh['time_motionless'] >= self.CF.Strategy['StopThreshold']) and \
                    (veh['looking_for_start'] == False):

                    veh['looking_for_start'] = True
                    veh['time_of_last_stop'] = tp

                    self.GeneratePDM(veh_data = veh, type = 1, time = tp)
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

                    self.GeneratePDM(veh_data = veh, type = 2, time = tp)
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

                    self.GeneratePDM(veh_data = veh, type = 3, time = tp)

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
    def GeneratePDM(self, veh_data, type, time):

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
            'num' : len(self.PDMs) + 1,
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
             'transmission_received_time' : -1
        }

        self.PDMs.append(SS)


        #9.1 Manage Vehicle Buffer Contents
        if (veh_data["in_privacy_gap"] != True) and (SS["PSN"] != -1):
            self.PDMBuffer.AddSS(veh_data = veh_data,
                                SS = SS,
                                locT = time,
                                Snapshots = self.PDMs,
                                CF = self.CF)
        else:
            self.PDMBuffer.DeleteSSinLog(SS = SS, locT = time, reason = 3, Snapshots = self.PDMs)


    #-------------------------------------------------------------------------
    def CheckCellular(self, veh_data, tp):
        """
        Checks to see if a PDM or BSM message can be sent via cellular for the given vehicle
        in the given time

        :param veh_data: The vehicle to check
        :param tp: The time period to check in
        """

        if self.CF.Control["OutputLevel"] >= 3:
            logger.debug('Checking for vehicles with enough snapshots in their buffer to transmit via cellular')

        #Set Default values if no region
        if self.regions is None:
            latency = 0.0
            loss_percent = 0.0
            mintransmit_PDM = 1
        else:
            latency = self.regions.default_latency
            loss_percent = self.regions.default_loss
            mintransmit_PDM = self.regions.min_PDM_to_transmit
        region_name = 'Cellular_Default'


        if veh_data['BSM_equipped'] and (veh_data['dsrc_transmit_bsm'] == False) and veh_data['cellular_enabled']:
            if float(self.CF.Strategy['BSMFrequencyCellular']) > 0.0:
                if veh_data['prev_time_BSM_cellular_transmit'] + float(self.CF.Strategy['BSMFrequencyCellular']) <= tp:
                    if self.randomgen['LossPercent'] > loss_percent:
                        self.GenerateTransmitBSM(veh_data=veh_data,
                                        transTo = region_name,
                                        isCellular= True,
                                        isRSE = False)
                        veh_data['prev_time_BSM_cellular_transmit'] = tp

            else:
                if self.randomgen['LossPercent'] > loss_percent:
                    self.GenerateTransmitBSM(veh_data=veh_data,
                                        transTo = region_name,
                                        isCellular= True,
                                        isRSE = False)


        if veh_data['PDM_equipped'] and (tp % 1 == 0) and veh_data['cellular_enabled']:

            if float(veh_data['prev_time_PDM_cellular_transmit']) + float(self.CF.Strategy['PDMFrequencyCellular']) <= tp:

                if self.CF.Control["OutputLevel"] >= 3:
                    logger.debug('Checking for cellular region at time %d'% veh_data['time'])

                #Check if vehicle is within a defined cellular region
                if self.regions is not None:
                    for region in self.regions.cell_regions:
                        if region.in_region(veh_data['location_x'], veh_data['location_y']):
                            #Assign the defined regions loss percentage and latency
                            latency = float(region.latency)
                            loss_percent = float(region.loss)
                            region_name = region.title
                            break

                if self.CF.Control["OutputLevel"] >= 3:
                    logger.debug('Checking for mininum number of SS to transmit')

                #If PDM buffer has the minimum number of snapshots
                if (self.PDMBuffer.BufferCount(veh_data['vehicle_ID']) >= mintransmit_PDM):
                    if veh_data["time"] != 0:

                        #By random number generator, determine if snapshot transmission is successful. Else delete snapshots.
                        if self.randomgen['LossPercent'] > loss_percent:

                            if self.CF.Control["OutputLevel"] >= 2:
                                 logger.debug("%s SS transmitted at time %d via cellular from vehicle ID: %s" % \
                                       (self.PDMBuffer.BufferCount(veh_data['vehicle_ID']), veh_data["time"], veh_data['vehicle_ID']))

                            self.PDMBuffer.TransmitPDM(veh_data=veh_data,
                                                       transTo=region_name,
                                                       isCellular=True,
                                                       tp = veh_data["time"],
                                                       Snapshots=self.PDMs,
                                                       latency=latency,
                                                       CF=self.CF)

                        else:
                            #Delete reason 5: transmission lost
                            self.PDMBuffer.ClearBuffer(vehicleID = veh_data['vehicle_ID'],
                                                        locT = veh_data["time"],
                                                        Snapshots = self.PDMs,
                                                        reason = 5,
                                                        transmitted_to = -1,
                                                        transTime = veh_data["time"])

                        veh_data['prev_time_PDM_cellular_transmit']= veh_data["time"]


#-------------------------------------------------------------------------
    def CheckSPOTdevice(self, veh_data, tp):
        """
        Check for ITS Spot devices in range of the current vehicle
        :param veh_data: The current vehicle data
        :param tp: The current time period
        """

        Inrange_SPOTdevices = self.SPOT_tree.Find_range(veh_data['location_x'], veh_data['location_y'])
        clear_SPOT_buffer = False

        for SPOT in Inrange_SPOTdevices:

            if veh_data['vehicle_ID'] in self.SPOTBuffer.ActiveBuffers.keys():
                travelSPOTs, behaviorSPOTs = self.SPOTBuffer.TransmitSPOTBuffer(veh_data)
                if (len(travelSPOTs)+len(behaviorSPOTs)) > 0:
                    self.TravelSPOTmsgs.extend(travelSPOTs)
                    self.BehaviorSPOTmsgs.extend(behaviorSPOTs)
                    clear_SPOT_buffer = True
                    veh_data['SPOT_trans_tp'] = tp
                    if self.CF.Control["OutputLevel"] >= 2:
                        logger.debug("%s ITS Spot messages transmitted at time %d from vehicle ID: %s" % \
                            ((len(travelSPOTs)+len(behaviorSPOTs)), veh_data["time"], veh_data['vehicle_ID']))

        if clear_SPOT_buffer:
            self.SPOTBuffer.ClearBuffer(veh_data['vehicle_ID'])


#-------------------------------------------------------------------------
    def CheckDSRC(self, veh_data, tp):
        """
        Checks to see if a PDM, BSM or CAM message can be sent via DSRC for the given vehicle
        in the given time

        :param veh_data: The vehicle to check
        :param tp: The time period to check in
        """
        #Select vehicles that are active and DSRC enabled (exclusively or dual)
        if ((tp % 1 ==0) and (veh_data['PDM_equipped']) and (veh_data['in_privacy_gap'] == False)) \
            or (veh_data['BSM_equipped']) or (veh_data['CAM_equipped']):


            Inrange_RSEs = self.RSE_tree.Find_range(veh_data['location_x'], veh_data['location_y'])


            transmit_BSM = False
            transmit_PDM = False
            transmit_SPOT = False

            if len(Inrange_RSEs) > 0:
                if veh_data['BSM_equipped']:
                    if (float(veh_data['prev_time_BSM_dsrc_transmit']) + float(self.CF.Strategy['BSMFrequencyDSRC'])) <= tp:
                        transmit_BSM = True

                if (tp % 1 ==0) and veh_data['PDM_equipped']:
                    if (float(veh_data['prev_time_PDM_dsrc_transmit']) + float(self.CF.Strategy['PDMFrequencyDSRC'])) <= tp:
                        transmit_PDM = True



            for RSE in Inrange_RSEs:

                    if veh_data['BSM_equipped'] and transmit_BSM:
                        if self.randomgen['LossPercent'] > self.RSEs.RSEList[RSE]['loss_rate']:
                            self.GenerateTransmitBSM(veh_data=veh_data,
                                                     transTo = RSE,
                                                     isCellular= False,
                                                     isRSE = True)
                            veh_data['dsrc_transmit_bsm'] = True
                            veh_data['prev_time_BSM_dsrc_transmit'] = tp


                    if transmit_PDM and (veh_data['vehicle_ID'] in self.PDMBuffer.ActiveBuffers.keys()) > 0:
                        if self.PDMBuffer.BufferCount(veh_data['vehicle_ID']) >= self.CF.Strategy['MinNumberofPDMtoTransmitViaDSRC']:
                            if self.randomgen['LossPercent'] > self.RSEs.RSEList[RSE]['loss_rate']:
                                veh_data['dsrc_transmit_pdm'] = True
                                veh_data['prev_time_PDM_dsrc_transmit'] = tp
                                self.RSETransmitPDM(veh_data, RSE)
                            else:
                                #Delete reason 5: transmission lost
                                self.PDMBuffer.ClearBuffer(vehicleID = veh_data['vehicle_ID'],
                                                            locT = tp,
                                                            Snapshots = self.PDMs,
                                                            reason = 5,
                                                            transmitted_to = -1,
                                                            transTime = -1)

                    if veh_data['CAM_equipped']:
                        if self.CheckCAMSnapshot(veh_data, tp):
                            if self.randomgen['LossPercent'] > self.RSEs.RSEList[RSE]['loss_rate']:
                                self.GenerateTransmitCAM(veh_data=veh_data,
                                                         transTo = RSE,
                                                         tp = tp)

    #-------------------------------------------------------------------------
    def RSETransmitPDM(self, veh_data, RSE):
        """
        Calls Transmit PDM to transmit to an RSE

        :param veh_data: The vehicle transmitting the message
        :param RSE: The RSE being transmitted to
        """

        if (veh_data["time"] != 0):
            if self.CF.Control["OutputLevel"] >= 2:
                logger.debug("%s PDMs transmitted at time %s to RSE:%s from vehicle:%s" %
                    (self.PDMBuffer.BufferCount(veh_data['vehicle_ID']), veh_data["time"], RSE, veh_data['vehicle_ID']))

            self.PDMBuffer.TransmitPDM(veh_data=veh_data,
                                       transTo=RSE,
                                       isCellular=False,
                                       tp = veh_data['time'],
                                       Snapshots=self.PDMs,
                                       CF=self.CF,
                                       latency= self.RSEs.RSEList[RSE]['latency'])


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
    def CheckRegion(self, veh, tp):
        """
        Checks to see which cellular region given vehicle is in at given time

        :param veh: Vehicle to check
        :param tp: Time to check in
        """

        event_values = {}

        # Loop through every event in every region
        for region in self.regions.Event_regions:
            for event, value in region.check_events(tp, veh['location_x'], veh['location_y']):
                if value == -1234:
                    value = self.tbl.db[veh['vehicle_ID']][event]
                if event in event_values:
                    #Only replace event value if Event is True, or the vehicle event field is currently default (-9999)
                    if int(event_values[event]) == 0 or float(event_values[event]) == -9999:
                        event_values[event] = value
                else:
                    event_values[event] = value

        for event in event_values.keys():
            veh[event] = event_values[event]
        event_values.clear()



    #-------------------------------------------------------------------------
    def CheckCAMSnapshot(self, veh, tp):
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
    def GenerateTransmitCAM(self, veh_data, transTo, tp):
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
                'stationID' : veh_data['PSN'],
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
            self.CAMs.append(CAM)

            veh_data['last_CAM_distance'] = veh_data['total_dist_traveled']
            veh_data['last_CAM_speed'] = veh_data['speed']
            veh_data['last_CAM_heading'] = veh_data['heading']
            veh_data['last_CAM_time'] = tp