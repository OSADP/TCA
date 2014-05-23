#Standard
import unittest

#TCA
from TCANetData import CLNetData
from TCABuffer import CLBuffer
from TCACore import Chk_Range, report_errors, Chk_Cellular_Range, Get_Heading


class TCA_Algorithm:
    def __init__(self, CF):
        #Load RSE Data
        self.RSE = CLNetData()
        if CF.Control["RSELocationFile"] is not None:
            errors = self.RSE.RSELoad(CF.Control["RSELocationFile"], CF)
            report_errors(errors)

        #Each Vehicle RSE list
        self.VehicleRSE = {}

        #Buffer Manager for Snapshots and BSMs
        self.SSBuffer = CLBuffer(CF.Strategy['TotalCapacity'])
        self.BSMBuffer = CLBuffer(CF.Strategy['TotalCapacity'])

        #Master Snapshot Class
        self.Snapshots = []

        #Master BSM Class
        self.BSMs = []

    def PSNCheck(self, df, timeStamp, RandomGen, CF):

        #4.1 check whether the distance or time has expired if not in gap
        select = df[(df['in_privacy_gap'] == False) & df['active']
            & ((df['time_stamp_of_ID'] + CF.Strategy ['TimeBetweenPSNSwitches']) <= timeStamp)
            & ((df['PSN_distance_travelled'] > CF.Strategy["DistanceBetweenPSNSwitches"]))]

        df['PSN_change_ID'][select.index] = 1

        #4.3 Generate dummy PSN if change is necessary
        select = df[(df['in_privacy_gap'] == False) & df['active']
            & ((df['time_stamp_of_ID'] + CF.Strategy ['TimeBetweenPSNSwitches']) <= timeStamp)
            & (df['PSN_distance_travelled'] > CF.Strategy["DistanceBetweenPSNSwitches"]) & (df['PSN_change_ID'] == 1)]
        df['temp_PSN'][select.index] = -1
        df['time_stamp_of_ID'][select.index] = timeStamp
        df['PSN_distance_travelled'][select.index] = 0

        #4.4 Check for Gap  (Note if CF.Strategy["Gap"]=0 then no Gaps are added)
        if CF.Strategy["Gap"] == 1:
            for i in sorted(select.index):
                df['time_in_privacy_gap'][i] = timeStamp +  RandomGen['GapTimeout']
                df['distance_in_privacy_gap'][i] = RandomGen['GapDistance']
            df['privacy_gap_start'][select.index] = timeStamp
            df['distance_travelled_in_gap'][select.index] = 0 #initialize back to zero with new Gap start
            df['in_privacy_gap'][select.index] = True
        else:
            for i in sorted(select.index):
                df['temp_PSN'][i] = RandomGen['psn']
                if CF.Control["OutputLevel"] >= 2:
                    print "PSN changed to %d for vehicle ID %s at time %s" % (df['temp_PSN'][i],
                        i, timeStamp)


        #4.5 Check to see if privacy gap has expired; generate new PSN
        if CF.Strategy["Gap"] == 1:
            #Only select those with in_privacy_gap == True and not changed in any previous step
            # Find vehicles where the distance has expired
            select = df[(df['in_privacy_gap'] == True) & df['active']
                & (df['PSN_change_ID'] == 0)
                & (df['distance_travelled_in_gap'] > df['distance_in_privacy_gap'])]
            for i in sorted(select.index):
                df['temp_PSN'][i] = RandomGen['psn']
            df['PSN_distance_travelled'][select.index] = 0
            df['time_stamp_of_ID'][select.index] = timeStamp
            df['in_privacy_gap'][select.index] = False

            # Find vehicles where the time has expired
            select = df[(df['in_privacy_gap'] == True) & df['active']
                & (df['PSN_change_ID'] == 0)
                & (timeStamp >= df['time_in_privacy_gap'])]
            for i in sorted(select.index):
                df['temp_PSN'][i] = RandomGen['psn']
            df['PSN_distance_travelled'][select.index] = 0
            df['time_stamp_of_ID'][select.index] = timeStamp
            df['in_privacy_gap'][select.index] = False

        #Set all change IDs to 0
        df['PSN_change_ID'] = 0


    #2.0 Check Snapshot Trigger
    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def CheckSnapshot(self, df, timeStep, timeStamp, CF):

        #TODO Find better way to access only active vehicles maybe new index
        # df = df[df['active']]
        df_active = df[(df['active'])]
        df_activeBSM = df[(df['active'])]

        #if CF.Strategy["BSMFlag"]:
        for i in df_active[(df['BSM_equipped'])].index:
            bsm = df_active.ix[i]
            if CF.Control['OutputLevel'] >= 2:
                print "BSM generated for vehicle ID %s at time %s" % (bsm['vehicle_ID'],timeStamp)
            self.GenerateBSM(bsm['vehicle_ID'], timeStamp, bsm, CF)

        if len(df_active[(df['PDM_equipped'])]) > 0:
            #2.1 Stop Trigger
            #2.1.1
            #Query all vehicles currently with speed of greater than zero and set their motionless value to zero.
            df['time_motionless'][df['speed'] > 0] = 0

            #Query all vehicles with speed of zero and add timeStep to its motionless value
            df['time_motionless'][df['speed'] == 0] += timeStep
            #Query all vehicles whose time since last stop recored is greater than Stop Lag,
            #whose Motionless value is greater than Stop Threshold and whose not looking
            #for a start and mark that a stop snapshot was taken and update the time since last stop and distance
            #since last stop.
            df_stops = df[(timeStamp - df['time_of_last_stop'] >= CF.Strategy['StopLag'])
                       & (df['time_motionless'] >= CF.Strategy['StopThreshold'])
                       & (df['looking_for_start'] == False) & df['active'] & df['PDM_equipped']]

            df['looking_for_start'][df_stops.index] = True

            df['time_of_last_stop'][df_stops.index] = timeStamp


            for i in sorted(df_stops.index):
                snapshot = df_stops.ix[i]
                if CF.Control["OutputLevel"] >= 2:
                    print 'Stop SS Created for Vehicle ID %s' % (snapshot['vehicle_ID'])
                self.GenerateSS(snapshot['vehicle_ID'], 1, timeStamp, snapshot, CF)

            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            #2.2 Start Trigger
            #2.2.1
            #Query all vehicles that currently have their looking for a start value set to true and whose speed
            #is greater than Start Threshold and mark that a start snapshot was taken and revert looking for a
            #start to false
            df_starts = df[(df['looking_for_start'] == True) & df['PDM_equipped']
                    & (df['speed'] >= CF.Strategy['StartThreshold']) & df['active']]

            df['looking_for_start'][df_starts.index] = False
            df['time_of_start_snapshot'][df_starts.index] = timeStamp

            for i in sorted(df_starts.index):
                snapshot = df_starts.ix[i]
                if CF.Control["OutputLevel"] >= 2:
                    print 'Start SS Created for Vehicle ID %s' % (snapshot['vehicle_ID'])
                self.GenerateSS(snapshot['vehicle_ID'], 2, timeStamp, snapshot, CF)


            #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
            #2.3 Periodic Trigger
            #2.3.1 and #2.3.2 (speed exception)
            #Query all vehicles that have not taken a start or stop snapshot, do not have their looking for
            #a start value set for true and whose time until their next periodic snapshot is <= the current time
            #and mark that a periodic snapshot was taken and re-calculate the time until the next periodic.
            df_periodic = df[(df['looking_for_start'] == False) & df['PDM_equipped']
                        & (df['time_to_next_periodic'] <= timeStamp) & df['active']]
            df['time_of_periodic_snapshot'][df_periodic.index] = timeStamp


            for i in sorted(df_periodic.index):
                if i in df_starts.index:
                    continue
                snapshot = df_periodic.ix[i]
                if CF.Control["OutputLevel"] >= 2:
                    print 'Periodic SS Created for Vehicle ID %s' % (snapshot['vehicle_ID'])
                self.GenerateSS(snapshot['vehicle_ID'], 3, timeStamp, snapshot, CF)
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
    def GenerateSS(self, TID, type, time, snapshot, CF):

        #create new Snapshot
        SS = dict()

        #9.0 Update Snapshot log

        SS["Tnum"] = TID
        SS["num"] = len(self.Snapshots) + 1
        SS["time"] = time
        SS['localtime'] = time
        SS["VID"] = snapshot['temp_PSN']
        SS["spd"] = snapshot["speed"]
        SS["x"] = snapshot['location_x']
        SS["y"] = snapshot['location_y']

        SS["lastRSE"] = 0
        SS["type"] = type
        if snapshot["in_privacy_gap"] == False:
            SS["transtime"] = - 1
            SS["transRSE"] = - 1
        else:
            SS["transtime"] = snapshot["distance_in_privacy_gap"]
            SS["transRSE"] = snapshot["time_in_privacy_gap"]

        SS["deltime"] = 0
        SS["delreason"] = 0
        SS["transmission_received_time"] = -1

        #Add Snap Shot to Main SS List
        self.Snapshots.append(SS)

        #9.1 Manage Buffer Contents
        if (snapshot["in_privacy_gap"] != True) and (SS["VID"] != -1):
            self.SSBuffer.AddSS(TID, SS, time, self.Snapshots, CF, False)
        else:
            self.SSBuffer.DeleteSSinLog(SS, time, -1, self.Snapshots)

    #-------------------------------------------------------------------------
    def GenerateBSM(self, TID, time, bsm, CF):
        #create new BWM
        BSM = {}

        #Update BSM log
        BSM["Tnum"] = TID
        BSM["VID"] = bsm['temp_PSN']
        BSM["num"] = len(self.BSMs) + 1
        BSM["localtime"] = time
        BSM["type"] = 4        #type 4 : BSM
        BSM["spd"] = bsm['speed']
        BSM["x"] = bsm['location_x']
        BSM["y"] = bsm['location_y']
        BSM["deltime"] = 0
        BSM["delreason"] = 0
        BSM["lastRSE"] = 0
        BSM["transtime"] = - 1
        BSM["transRSE"] = - 1
        BSM["avg_accel"] = bsm['average_acceleration']
        BSM["heading"] = Get_Heading(bsm['location_x_last'], bsm['location_y_last'],bsm['location_x'], bsm['location_y'])

        #Add BSM to the Main BSM list
        self.BSMs.append(BSM)

        #Manage the buffer
        self.BSMBuffer.AddSS(TID, BSM, time, self.BSMs, CF, True)

    #-------------------------------------------------------------------------
    #check cellular
    def CheckCellular(self, df, CF, RandomGen):
        typeBSM = CF.Strategy["BSMCellularFlag"]
        typePDM = CF.Strategy["PDMCellularFlag"]
        df_cellular = df[(df['cellular_enabled'] == True) & df['active']]

        #Set Default values
        latency = CF.Strategy["DefaultLatency"]
        loss_percent = CF.Strategy["DefaultLossPercent"]
        region_name = 'Cellular_Default'

        if CF.Control["OutputLevel"] >= 3:
            print 'Checking for vehicles with enough snapshots in their buffer to transmit via cellular'

        #Loop through each cellular vehicle
        for vehicle_id in sorted(df_cellular.index):
            entry = df_cellular.ix[vehicle_id]

            if CF.Control["OutputLevel"] >= 3:
                print 'Checking for cellular region at time ',entry['time']

            #Check if vehicle is within a defined cellular region
            region_list = CF.Strategy["Regions"]
            for region in region_list:
                if Chk_Cellular_Range(region["X1"],region["Y1"],region["X2"],region["Y2"],entry['location_x'],entry['location_y']):
                    #Assign the defined regions loss percentage and latency
                    latency = region["Latency"]
                    loss_percent = region["LossPercent"]
                    region_name = region["Name"]
                    break


            if CF.Control["OutputLevel"] >= 3:
                print 'Checking for mininum number of SS to transmit'

            #If PDM buffer has the minimum number of snapshots
            if typePDM:
                if (self.SSBuffer.BufferCount(entry['vehicle_ID'],False) >= CF.Strategy["MinNumberofSStoTransmitViaCellular"]):
                    if entry["time"] != 0:

                        #By random number generator, determine if snapshot transmission is successful. Else delete snapshots.
                        if RandomGen['LossPercent'] > loss_percent:

                            if CF.Control["OutputLevel"] >= 3:
                                 print "%s SS transmitted at time %d via cellular" % \
                                       (self.SSBuffer.BufferCount(entry['vehicle_ID'],False),entry["time"])
                            
                            self.SSBuffer.Transmit(entry['vehicle_ID'],region_name, entry, self.Snapshots, CF, latency, False)
                            df['time_of_last_transmit'][df['vehicle_ID'] == entry['vehicle_ID']] = entry["time"]
                        else:
                            #Delete reason 5: transmission lost
                            self.SSBuffer.ClearBuffer(entry['vehicle_ID'],entry["time"],self.Snapshots,5,region_name,entry["time"])
            #If BSM buffer has the minimum number of snapshots
            if typeBSM:
                if (self.BSMBuffer.BufferCount(entry['vehicle_ID'],True) >= CF.Strategy["MinNumberofSStoTransmitViaCellular"]):
                    if entry["time"] != 0:

                        #By random number generator, determine if snapshot transmission is successful. Else delete snapshots.
                        if RandomGen['LossPercent'] > loss_percent:

                            if CF.Control["OutputLevel"] >= 3:
                                 print "%s BSM transmitted at time %d via cellular" % \
                                       (self.BSMBuffer.BufferCount(entry['vehicle_ID'],True),entry["time"])
                            
                            self.BSMBuffer.Transmit(entry['vehicle_ID'],region_name, entry, self.BSMs, CF, latency, True)
                            df['time_of_last_transmit'][df['vehicle_ID'] == entry['vehicle_ID']] = entry["time"]
                        else:
                            #Delete reason 5: transmission lost
                            self.BSMBuffer.ClearBuffer(entry['vehicle_ID'],entry["time"],self.BSMs,5,region_name,entry["time"])

    #-------------------------------------------------------------------------
    #check the distance to RSEs
    def ChkRSERange(self, df, CF):

        df_active = df[(df['active'])]
        #3.1 and 3.2
        for vehicle_id in sorted(df_active.index):
            entry = df_active.ix[vehicle_id]

            UseableRSE = []
            UseableBSMRSE = []


            if CF.Control["OutputLevel"] >= 3:
                print 'Checking for RSE range at time',entry['time']

            #Check distance to each RSEList
            for rse_name in self.RSE.RSEList.keys():

                #check if vehicle is already in rse list
                if vehicle_id not in [x for x in self.RSE.RSEList[rse_name]['interactcount'].keys()]:
                     self.RSE.RSEList[rse_name]['inrange'][vehicle_id] = False
                     self.RSE.RSEList[rse_name]['interactcount'][vehicle_id]  =  0
                     self.RSE.RSEList[rse_name]['time'][vehicle_id] =  0
                     self.RSE.RSEList[rse_name]['range'][vehicle_id] = 0

                Ran = Chk_Range(entry["location_x"], entry["location_y"],
                                self.RSE.RSEList[rse_name]["x"], self.RSE.RSEList[rse_name]["y"])

                self.RSE.RSEList[rse_name]["range"][vehicle_id] =  Ran

                #check to see if it's in range and less then the number Reports
                if  (Ran <= CF.Strategy["MinRSERange"]) and \
                    (self.RSE.RSEList[rse_name]['interactcount'][vehicle_id] < CF.Strategy["RSEReports"]):
                            UseableRSE.append(rse_name)
                            UseableBSMRSE.append(rse_name)
                elif  (Ran <= CF.Strategy["MinRSERange"]):
                    self.RSE.RSEList[rse_name]['interactcount'][vehicle_id] += 1
                    UseableBSMRSE.append(rse_name)


                #check if RSE is in range
                if Ran <= CF.Strategy['MaxRSERange']:
                    #Set RSE in range to true
                     self.RSE.RSEList[rse_name]["inrange"][vehicle_id] = True
                else:
                    #Set RSE in range to false
                    self.RSE.RSEList[rse_name]["inrange"][vehicle_id] = False
                    #Set RSE back to available
                    self.RSE.RSEList[rse_name]["interactcount"][vehicle_id]= 0


            if (len(UseableRSE) > 0 and CF.Control["OutputLevel"] >= 2) or CF.Control["OutputLevel"]>= 3:
                print len(UseableRSE),'RSEs found in range:',UseableRSE

            #Transmit BSMs via DSRC if BSM messaging is turned on
            if entry['BSM_equipped'] and not entry['cellular_enabled']: #CF.Strategy["BSMFlag"] and not CF.Strategy["BSMCellularFlag"]:
                self.RSETransmit(df, vehicle_id, CF, UseableBSMRSE, True, entry, self.BSMBuffer, self.BSMs)
            #Else: Transmit PDMs via DSRC
            if entry['PDM_equipped'] and not entry['cellular_enabled']: #CF.Strategy["PDMFlag"] and not CF.Strategy["PDMCellularFlag"]:
                if self.SSBuffer.GetLastRSE(entry['vehicle_ID']) in UseableRSE:
                        UseableRSE.remove(self.SSBuffer.GetLastRSE(entry['vehicle_ID']))
                self.RSETransmit(df, vehicle_id, CF, UseableRSE, False, entry, self.SSBuffer, self.Snapshots)

    #-------------------------------------------------------------------------
    def RSETransmit(self, df, vehicle_id, CF, UseableRSE, typeBSM, entry, Buffer, Snapshots):
        if (len(UseableRSE) > 0) and (Buffer.BufferCount(entry['vehicle_ID'], typeBSM) >= CF.Strategy["MinNumberofSStoTransmit"]):
            #find closet RSE
            MinRange = CF.Strategy["MinRSERange"]
            for rse_name in UseableRSE:
                if self.RSE.RSEList[rse_name]["range"][vehicle_id] <= MinRange:
                    MinRSE = rse_name
                    MinRange = self.RSE.RSEList[rse_name]["range"][vehicle_id]

            if not typeBSM:
                self.RSE.RSEList[MinRSE]["time"][vehicle_id]  = entry["time"]
                self.RSE.RSEList[MinRSE]['interactcount'][vehicle_id] += 1

            if (entry["time"] != 0):
                        if CF.Control["OutputLevel"] >= 3:
                            print "%s SS transmitted at time %s to RSE:%s" % \
                                (Buffer.BufferCount(entry['vehicle_ID'], typeBSM), entry["time"], MinRSE)
                        Buffer.Transmit(entry['vehicle_ID'], MinRSE, entry, Snapshots, CF, 0, typeBSM)
                        df['time_of_last_transmit'][df['vehicle_ID'] == entry['vehicle_ID']] = entry["time"]
