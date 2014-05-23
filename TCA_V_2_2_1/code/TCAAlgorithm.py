#Standard
import unittest

#external
import pandas as pd

#TCA
from TCANetData import CLNetData
from TCABuffer import CLBuffer, CLBSMAllBuffer
from TCASpacePartitioning import Find_RSE_range
from TCACore import Chk_Range, report_errors, Chk_Cellular_Range, Get_Heading, logger, Timer


class TCA_Algorithm:
    def __init__(self, CF, BSM_limit = 800000):
        #Load RSE Data
        self.RSE = CLNetData()
        if CF.Control["RSELocationFile"] is not None:
            errors = self.RSE.RSELoad(CF.Control["RSELocationFile"], CF)
            report_errors(errors)

        #Each Vehicle RSE list
        self.VehicleRSE = {}

        #Buffer Manager for Snapshots and BSMs
        self.PDMBuffer = CLBuffer(CF.Strategy['TotalCapacity'])

        #Master Snapshot Classes for hold all SS
        self.PDMs = []
        self.BSMs = []

        #Limit of BSM list before printing to a file
        self.BSM_limit = BSM_limit


        self.timer = Timer(enabled=True)

    #-------------------------------------------------------------------------
    def GenerateTransmitBSM(self, row, transTo, BSMs, Outlevel, AccelColumn, regions, RandomGen=None, latency=0, checkCellular=False, isRSE=False):
        if row['BSM_equipped']:
            transmitted = True

            #Check if vehicle is within a defined cellular region
            if regions is not None and checkCellular:
                if len(regions.cell_regions) > 0:
                    for region in regions.cell_regions:
                        if region.in_region(row['location_x'],row['location_y']):
                            #Assign the defined regions loss percentage and latency
                            latency = float(region.latency)
                            if RandomGen['LossPercent'] < float(region.loss):
                                transmitted = False
                            transTo = region.title

            if isRSE and RandomGen['LossPercent'] <= self.RSE.RSEList[transTo][3]:
                transmitted = False

            if transmitted:
                BSM = {
                    'Vehicle_ID' : row['vehicle_ID'],
                    'VID' : row['temp_PSN'],
                    'localtime' : row['time'],
                    'spd' : row['speed'],
                    'x' : row['location_x'],
                    'y' : row['location_y'],
                    'transtime' : row['time'],
                    'transTo' : transTo,
                    'avg_accel' : row['average_acceleration'],
                    'brakeStatus' : row["brake_status"],
                    'brakePressure' : row['brake_pressure'],
                    'hardBraking' : row['hard_braking'],
                    'transmission_received_time' : row['time'] + latency
                }
                if AccelColumn != None:
                    BSM["instant_accel"] = row['accel_instantaneous']
                BSM["heading"] = Get_Heading(row['location_y_last'], row['location_x_last'],
                                             row['location_y'], row['location_x'])
                if regions is not None:
                    for region_name in regions.Event_titles:
                        BSM[region_name] = row[region_name]

                #Add BSM to the Main BSM list
                BSMs.append(BSM)


    #-------------------------------------------------------------------------
    def PSNCheck(self, df, timeStamp, RandomGen, CF):

        def change_PSN(select, df, timeStamp, RandomGen, CF ):
            for i in sorted(select.index):
                df['temp_PSN'][i] = RandomGen['psn']
                df['PSN_distance_to_change'][i] = df['total_dist_traveled'][i]  + CF.Strategy["DistanceBetweenPSNSwitches"]
                df['PSN_time_to_end_of_PSN'][i] = timeStamp + CF.Strategy['TimeBetweenPSNSwitches']
                if CF.Control["OutputLevel"] >= 2:
                    logger.debug("PSN changed to %d for vehicle ID %s at time %s because of RSE transmission" % (df['temp_PSN'][i],
                        i, timeStamp))

        def start_gap(select, df, timeStamp, RandomGen, CF):
            for i in sorted(select.index):
                df['temp_PSN'][i] = -1
                df['PSN_time_to_end_gap'][i] = timeStamp +  RandomGen['GapTimeout']
                df['PSN_distance_to_end_of_gap'][i] =  df['total_dist_traveled'][i] + RandomGen['GapDistance']
                if CF.Control["OutputLevel"] >= 2:
                    logger.debug("Vehicle ID %s at time %s enters PSN privacy gap because of RSE transmission" % (i, timeStamp))
                df['privacy_gap_start'][select.index] = timeStamp
                df['in_privacy_gap'][select.index] = True

        #Change PSN or activate privacy gap if vehicle has transmitted to an RSE and is PDM equipped
        select = df[df['active'] & df['dsrc_transmit_pdm'] & df['PDM_equipped'] & (df['time_of_last_transmit'] == timeStamp)]



        if len(select) > 0:
            if CF.Strategy["GapMaxDistance"] == 0 or CF.Strategy["GapMaxTime"] == 0:
                change_PSN(select, df, timeStamp, RandomGen, CF )
            else:
                start_gap(select, df, timeStamp, RandomGen, CF)


        #4.1 check whether the distance and time has expired of current PSN if not in gap
        select = df[(df['in_privacy_gap'] == False) & df['active'] & df['PDM_equipped']
            & ((timeStamp >= df['PSN_time_to_end_of_PSN']))
            & ((df['total_dist_traveled'] >= df['PSN_distance_to_change']))]


        #4.4 Check for Gap  (Note if CF.Strategy["Gap"]=0 then no Gaps are added)
        if len(select) > 0:
            if CF.Strategy["Gap"] == 1:
                start_gap(select, df, timeStamp, RandomGen, CF)
            else:
                change_PSN(select, df, timeStamp, RandomGen, CF )


        #4.5 Check to see if privacy gap has expired; generate new PSN
        select = df[(df['in_privacy_gap'] == True) & df['active'] & df['PDM_equipped']
            & ((df['total_dist_traveled'] >= df['PSN_distance_to_end_of_gap'])
            | (timeStamp >= df['PSN_time_to_end_gap']))].sort('vehicle_ID') #& (df['PSN_change_ID'] == 0)


        if len(select) > 0:
            change_PSN(select, df, timeStamp, RandomGen, CF )
            df['in_privacy_gap'][select.index] = False
            if CF.Control["OutputLevel"] >= 2:
                for i in sorted(select.index):
                    logger.debug("PSN changed to %d for vehicle ID %s at time %s because privacy gap expired" %
                                 (df['temp_PSN'][i], i, timeStamp))

    #2.0 Check Snapshot Trigger
    #-------------------------------------------------------------------------
    def CheckPDMSnapshot(self, df, timeStep, timeStamp, CF, regions):

        #df = df[df['active']]
        #Query only vehicles that have been active in the network for the user-defined amount of time or distance
        #The default J2735 values are: 500m or 120 seconds
        df_active = df[(df['active'] & df['PDM_equipped'] &
                    ((df['total_time_in_network'] >= CF.Strategy['TimeBeforePDMCollection']) |
                    (df['total_dist_traveled'] >= CF.Strategy['DistanceBeforePDMCollection'])))]
        # df_activeBSM = df[(df['active']) & df['BSM_equipped']]

        # df_activeBSM.apply(lambda x: self.GenerateBSM(x, timeStamp, CF, regions), axis=1)

        if timeStamp % 1 == 0:
            if len(df_active[(df['PDM_equipped'])]) > 0:
                #2.1 Stop Trigger
                #2.1.1
                #Query all vehicles currently with speed of greater than zero and set their motionless value to zero.
                df['time_motionless'][(df_active[(df_active['speed'] > 0)]).index] = 0

                #Query all vehicles with speed of zero and add timeStep to its motionless value
                df['time_motionless'][(df_active[(df_active['speed'] == 0)]).index] += 1
                #Query all vehicles whose time since last stop recorded is greater than Stop Lag,
                #whose Motionless value is greater than Stop Threshold and whose not looking
                #for a start and mark that a stop snapshot was taken and update the time since last stop and distance
                #since last stop.
                df_stops = df_active[(timeStamp - df_active['time_of_last_stop'] >= CF.Strategy['StopLag'])
                           & (df_active['time_motionless'] >= CF.Strategy['StopThreshold'])
                           & (df_active['looking_for_start'] == False)
                           & df_active['PDM_equipped']].sort('vehicle_ID')
                df['looking_for_start'][df_stops.index] = True
                df['time_of_last_stop'][df_stops.index] = timeStamp


                for i in sorted(df_stops.index):
                    snapshot = df_stops.ix[i]
                    if CF.Control["OutputLevel"] >= 2:
                        logger.debug('Stop SS Created for Vehicle ID %s at time:%s' % (snapshot['vehicle_ID'],timeStamp))
                    self.GeneratePDM(snapshot['vehicle_ID'], 1, timeStamp, snapshot, CF)

                #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                #2.2 Start Trigger
                #2.2.1
                #Query all vehicles that currently have their looking for a start value set to true and whose speed
                #is greater than Start Threshold and mark that a start snapshot was taken and revert looking for a
                #start to false
                df_starts = df_active[(df_active['looking_for_start'] == True)
                            & (df_active['speed'] >= CF.Strategy['StartThreshold'])].sort('vehicle_ID')

                df['looking_for_start'][df_starts.index] = False
                df['time_of_start_snapshot'][df_starts.index] = timeStamp

                for i in df_starts.index:
                    snapshot = df_starts.ix[i]
                    self.GeneratePDM(snapshot['vehicle_ID'], 2, timeStamp, snapshot, CF)


                #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
                #2.3 Periodic Trigger
                #2.3.1 and #2.3.2 (speed exception)
                #Query all vehicles that have not taken a start or stop snapshot, do not have their looking for
                #a start value set for true and whose time until their next periodic snapshot is <= the current time
                #and mark that a periodic snapshot was taken and re-calculate the time until the next periodic.
                df_periodic = df_active[(df_active['looking_for_start'] == False)
                              & (df_active['time_to_next_periodic'] <= timeStamp)].sort('vehicle_ID')

                df['time_of_periodic_snapshot'][df_periodic.index] = timeStamp



                for i in df_periodic.index:

                    if i in df_starts.index:
                        continue


                    snapshot = df_periodic.ix[i]
                    self.GeneratePDM(snapshot['vehicle_ID'], 3, timeStamp, snapshot, CF)

                    if CF.Control["OutputLevel"] >= 2:
                        logger.debug('Periodic SS Created for Vehicle ID %s at time:%s' % (snapshot['vehicle_ID'], timeStamp))

                    #check for when the next check should be
                    if snapshot['speed'] <= CF.Strategy["LowSpeedThreshold"]:
                        IncreaseTime = CF.Strategy["ShortSpeedInterval"]
                    elif snapshot['speed'] >= CF.Strategy["HighSpeedThreshold"]:
                        IncreaseTime = CF.Strategy["LongSpeedInterval"]
                    else:         #Speed Interpolation
                        slope = (snapshot['speed'] - CF.Strategy["LowSpeedThreshold"]) / \
                                (CF.Strategy["HighSpeedThreshold"] - CF.Strategy["LowSpeedThreshold"])
                        IncreaseTime = round(CF.Strategy["ShortSpeedInterval"] + slope *
                                             (CF.Strategy["LongSpeedInterval"] - CF.Strategy["ShortSpeedInterval"]))


                    #increase time counter
                    df['time_to_next_periodic'][i] = timeStamp + IncreaseTime


    #-------------------------------------------------------------------------
    def GeneratePDM(self, VID, type, time, snapshot, CF):

        #create new Snapshot
        SS = {}

        if CF.Control["OutputLevel"] >= 3:
            print("PDM type %d created in vehicle %s" % (type, VID))
            logger.debug("PDM type %d created in vehicle %s" % (type, VID))

        #9.0 Update Snapshot log

        SS["VID"] = VID
        SS["num"] = len(self.PDMs) + 1
        SS["time"] = time
        SS['localtime'] = time
        SS["PSN"] = snapshot['temp_PSN']
        SS["spd"] = snapshot["speed"]
        SS["x"] = snapshot['location_x']
        SS["y"] = snapshot['location_y']

        if VID in self.PDMBuffer.ActiveBuffers.keys():
            SS["lastRSE"] = self.PDMBuffer.GetLastRSE(VID)
        else:
            SS["lastRSE"] = 0
        SS["type"] = type

        SS["transtime"] = - 1
        SS["transTo"] = - 1

        SS["deltime"] = 0
        SS["delreason"] = 0
        SS["transmission_received_time"] = -1

        #Add Snap Shot to Main SS List
        self.PDMs.append(SS)


        #9.1 Manage Vehicle Buffer Contents
        if (snapshot["in_privacy_gap"] != True) and (SS["PSN"] != -1):
            self.PDMBuffer.AddSS(VID, SS, time, self.PDMs, CF, False)
        else:
            self.PDMBuffer.DeleteSSinLog(SS, time, 3, self.PDMs)


    #-------------------------------------------------------------------------
    def CheckCellular(self, df, CF, RandomGen, checkPDM, pdm, tp, regions):

        if CF.Control["OutputLevel"] >= 3:
            logger.debug('Checking for vehicles with enough snapshots in their buffer to transmit via cellular')


        #Set Default values if no region
        if regions is None:
            latency = 0.0
            loss_percent = 0.0
            mintransmit_PDM = 4
        #
        else:
            latency = regions.default_latency
            loss_percent = regions.default_loss
            mintransmit_PDM = regions.min_PDM_to_transmit
        region_name = 'Cellular_Default'

        self.timer.start('alg_check_cell_select_vehicles')

        df_bsm_cellular = df[df['active']
                      & (df['cellular_enabled'] | df['dual_enabled'])
                      & (df['BSM_equipped'])
                      & (df['dsrc_transmit_bsm'] == False)

        ]

        self.timer.stop('alg_check_cell_select_vehicles')
        self.timer.start('alg_check_cell_create_BSMs')

        df_bsm_cellular.apply(lambda x: self.GenerateTransmitBSM(x, region_name,
                                                                 self.BSMs,
                                                                 CF.Control["OutputLevel"],
                                                                 CF.Control["AccelColumn"],
                                                                 regions,
                                                                 RandomGen,
                                                                 checkCellular=True), axis=1)
        self.timer.stop('alg_check_cell_create_BSMs')
        self.timer.start('alg_check_cell_create_PDMs')

        if pdm and checkPDM:

            df_pdm_cellular = df[df['active']
                          & (df['cellular_enabled'] | df['dual_enabled'])
                          & (df['PDM_equipped'])]


            #Loop through each cellular PDM vehicle
            for vehicle_id in sorted(df_pdm_cellular.index):
                entry = df_pdm_cellular.ix[vehicle_id]

                if CF.Control["OutputLevel"] >= 3:
                    logger.debug('Checking for cellular region at time %d'% entry['time'])

                #Check if vehicle is within a defined cellular region
                if regions is not None:
                    for region in regions.cell_regions:
                        if region.in_region(entry['location_x'],entry['location_y']):
                            #Assign the defined regions loss percentage and latency
                            latency = float(region.latency)
                            loss_percent = float(region.loss)
                            region_name = region.title
                            break

                if CF.Control["OutputLevel"] >= 3:
                    logger.debug('Checking for mininum number of SS to transmit')

                #If PDM buffer has the minimum number of snapshots
                if (self.PDMBuffer.BufferCount(entry['vehicle_ID']) >= mintransmit_PDM):
                    if entry["time"] != 0:

                        #By random number generator, determine if snapshot transmission is successful. Else delete snapshots.
                        if RandomGen['LossPercent'] > loss_percent:

                            if CF.Control["OutputLevel"] >= 2:
                                 logger.debug("%s SS transmitted at time %d via cellular from vehicle ID: %s" % \
                                       (self.PDMBuffer.BufferCount(entry['vehicle_ID']), entry["time"], entry['vehicle_ID']))

                            self.PDMBuffer.TransmitPDM(entry['vehicle_ID'], True, region_name, entry["time"], self.PDMs, CF, latency)

                            df['time_of_last_transmit'][df['vehicle_ID'] == entry['vehicle_ID']] = entry["time"]
                        else:
                            #Delete reason 5: transmission lost
                            self.PDMBuffer.ClearBuffer(entry['vehicle_ID'],entry["time"],self.PDMs,5,-1,entry["time"])

        self.timer.stop('alg_check_cell_create_PDMs')



    #-------------------------------------------------------------------------
    def CheckDSRC(self, df, CF, checkPDM, pdm, tp, regions, RandomGen):

        #Select vehicles that are active and DSRC enabled (exclusively or dual)
        self.timer.start('alg_check_dsrc_select_vehicles')
        if checkPDM and pdm:
            df_active = df[df['active']
                        & (df['in_privacy_gap'] == False)
                        & (df['DSRC_enabled'] | df['dual_enabled'])
                        & (df['BSM_equipped'] | (df['PDM_equipped']))]
        else:
            df_active = df[df['active']
                           & (df['DSRC_enabled'] | df['dual_enabled'])
                           & df['BSM_equipped']]

        self.timer.stop('alg_check_dsrc_select_vehicles')


        if len(df_active) > 0:

            self.timer.start('alg_check_dsrc_Find_RSE_Ranges')
            RSE_Ranges = Find_RSE_range(df_active, self.RSE, CF.Strategy["MinRSERange"] )
            self.timer.stop('alg_check_dsrc_Find_RSE_Ranges')

            self.timer.start('alg_check_dsrc_Transmit')
            for RSE in RSE_Ranges.keys():

                if len(RSE_Ranges[RSE]) > 0:

                    self.timer.start('alg_check_dsrc_create_BSMs')
                    rse_active = df_active.ix[RSE_Ranges[RSE]]
                    rse_active.apply(lambda x: self.GenerateTransmitBSM(x, RSE, self.BSMs, CF.Control["OutputLevel"],
                                                                    CF.Control["AccelColumn"],
                                                                    regions, RandomGen, self.RSE.RSEList[RSE][2],
                                                                    isRSE=True), axis=1)

                    df['dsrc_transmit_bsm'][RSE_Ranges[RSE]] = True
                    self.timer.stop('alg_check_dsrc_create_BSMs')
                    self.timer.start('alg_check_dsrc_create_PDMs')

                    if pdm and checkPDM:

                        for vehicle_id in RSE_Ranges[RSE]:
                            entry = df_active.loc[[vehicle_id]]
                            if entry['PDM_equipped'].any():
                                if self.PDMBuffer.BufferCount(vehicle_id) >= CF.Strategy["MinNumberofPDMtoTransmitViaDSRC"]:
                                    #By random number generator, determine if snapshot transmission is successful. Else delete snapshots.
                                    if RandomGen['LossPercent'] > self.RSE.RSEList[RSE][3]:
                                        df['dsrc_transmit_pdm'][vehicle_id] = True
                                        df['time_of_last_transmit'][vehicle_id] = entry["time"].values[0]
                                        self.RSETransmitPDM(df, vehicle_id, CF, RSE, entry, self.PDMBuffer, self.PDMs)
                                    else:
                                        #Delete reason 5: transmission lost
                                        self.PDMBuffer.ClearBuffer(vehicle_id, entry["time"].values[0], self.PDMs ,5
                                                                   ,-1 , entry["time"])

                    self.timer.stop('alg_check_dsrc_create_PDMs')

            self.timer.stop('alg_check_dsrc_Transmit')

    #-------------------------------------------------------------------------
    def RSETransmit(self, df, vehicle_id, CF, UseableRSE, typeBSM, entry, Buffer, Snapshots):

        if typeBSM:
            minNum = CF.Strategy["MinNumberofBSMSStoTransmitViaDSRC"]
        else:
            minNum = CF.Strategy["MinNumberofPDMSStoTransmitViaDSRC"]

        if (len(UseableRSE) > 0) and (Buffer.BufferCount(entry['vehicle_ID']) >= minNum):
            #find closest RSE
            MinRange = CF.Strategy["MinRSERange"]
            for rse_name in UseableRSE:
                if self.RSE.RSEList[rse_name]["range"][vehicle_id] <= MinRange:
                    MinRSE = rse_name
                    MinRange = self.RSE.RSEList[rse_name]["range"][vehicle_id]

            if not typeBSM:
                self.RSE.RSEList[MinRSE]["time"][vehicle_id]  = entry["time"]
                self.RSE.RSEList[MinRSE]['interactcount'][vehicle_id] += 1

            if (entry["time"] != 0):
                if CF.Control["OutputLevel"] >= 2:
                    SStype = 'PDMs'
                    if typeBSM:
                        SStype = 'BSMs'
                    logger.debug("%s %s transmitted at time %s to RSE:%s from vehicle:%s" %
                        (Buffer.BufferCount(entry['vehicle_ID']), SStype, entry["time"], MinRSE, entry['vehicle_ID']))
                Buffer.Transmit(entry['vehicle_ID'], False, MinRSE, entry, Snapshots, CF, 0, typeBSM)
                if not typeBSM:
                    df['time_of_last_transmit'][df['vehicle_ID'] == entry['vehicle_ID']] = entry["time"]
                    df['dsrc_transmit'][df['vehicle_ID'] == entry['vehicle_ID']] = True

    #-------------------------------------------------------------------------
    def RSETransmitPDM(self, df, vehicle_id, CF, RSE, entry, Buffer, Snapshots):

        if (entry["time"].values[0] != 0):
            if CF.Control["OutputLevel"] >= 2:
                logger.debug("%s PDMs transmitted at time %s to RSE:%s from vehicle:%s" %
                    (Buffer.BufferCount(vehicle_id), entry["time"].values[0], RSE,
                     entry['vehicle_ID']))

            self.timer.start('alg_PDM_Transmit_code')
            Buffer.TransmitPDM(vehicle_id, False, RSE, entry["time"].values[0], Snapshots, CF, self.RSE.RSEList[RSE][2])
            self.timer.stop('alg_PDM_Transmit_code')

    #-------------------------------------------------------------------------
    def CheckBrakes(self, df, CF):
        # Brake elements only apply to BSM vehicles
        df_active_BSM = df['active'] & df['BSM_equipped']


        # Set brake_status as applied if decelerating more than the defined threshold
        df['brake_status'][df_active_BSM & (df['accel_instantaneous'] <= CF.Strategy['BrakeThreshold'])] = '1111'
        df['brake_status'][df_active_BSM & (df['accel_instantaneous'] > CF.Strategy['BrakeThreshold'])] = '0000'

        # Only set the brake pressure is instantaneous acceleration is available
        if CF.Control['AccelColumn'] is not None and (len(df['brake_pressure'][df_active_BSM]) > 0):
            df['brake_pressure'][df_active_BSM] = df[df_active_BSM].apply(lambda row: self.CheckBrakeLevel(row),axis=1)

        # Set the hard braking (1: true, 0: false) if decelerating greater than 0.4g (J2735 standard) or approx. 12.9 ft/s^2
        df['hard_braking'][df['accel_instantaneous'] <= -12.869619] = 1
        df['hard_braking'][df['accel_instantaneous'] > -12.869619] = 0


    def CheckBrakeLevel(self, vehRow):
        if vehRow['accel_instantaneous'] <= 0:
            return vehRow['accel_instantaneous']
        else:
            return 0.0

    #-------------------------------------------------------------------------
    def CheckRegion(self, df, tp, CF, regions):
        self.timer.start('alg_CheckRegion')

        df_active_BSM = df['active'] & df['BSM_equipped']

        for vehicle_id in sorted(df[df_active_BSM].index):
            event_values = {}
            entry = df.loc[[vehicle_id]]

            # Loop through every event in every region
            for region in regions.Event_regions:
                for event, value in region.check_events(tp, entry['location_x'], entry['location_y']):
                    if value == -1234:
                        value = entry[event]
                    if event in event_values:
                        #Only replace event value if Event is True, or the vehicle event field is currently default (-9999)
                        if int(event_values[event]) == 0 or float(event_values[event]) == -9999:
                            event_values[event] = value
                    else:
                        event_values[event] = value

            self.timer.start('alg_setEventValues')
            for event in event_values.keys():
                df[event][vehicle_id] = event_values[event]
            event_values.clear()
            self.timer.stop('alg_setEventValues')

        self.timer.stop('alg_CheckRegion')
