#standard
import unittest


#-------------------------------------------------------------------------

class SPOTBuffer:
#-------------------------------------------------------------------------
    def __init__(self):
        """
        Initializes SPOTBuffer module

        """
        self.ActiveBuffers = {}
        self.SPOT_BEHAVIOR_LIMIT = 31

#-------------------------------------------------------------------------
    def AddSPOT(self, SPOT, type):
        """
        Adds SPOT message to buffer.

        :param SPOT: The dictionary containing SPOT message data
        :param type: The type of message, 1 if Travel Record, otherwise Behavior Record
        """
        vehicleID = SPOT['vehicle_ID']

        if vehicleID not in self.ActiveBuffers.keys():
            self.ActiveBuffers[vehicleID] = {'travel' : [],
                                            'behavior': []}

        if type == 1:
            self.ActiveBuffers[vehicleID]['travel'].append(SPOT)
        else:
            while len(self.ActiveBuffers[vehicleID]['behavior']) >= self.SPOT_BEHAVIOR_LIMIT:
                self.ActiveBuffers[vehicleID]['behavior'].pop(0)
            self.ActiveBuffers[vehicleID]['behavior'].append(SPOT)

    def TransmitSPOTBuffer(self, veh_data):
        """
        "Transmits" SPOT messages in given vehicle's buffer

        :param veh_data: The vehicle transmitting messages
        :return: A list of transmitted Travel Records and a list of transmitted Behavior Records
        """
        vehicleID = veh_data['vehicle_ID']
        transmitted_travel_list = []
        transmitted_behavior_list = []

        for SPOT in self.ActiveBuffers[vehicleID]['travel']:
            # Delete message generated more than 50 miles since last transmission
            if ((veh_data['total_dist_traveled'] - SPOT['dist_traveled']) / 5280) > 50:
                self.ActiveBuffers[vehicleID]['travel'].pop(0)

            else:
                transmitted_travel_list.append(SPOT)

        for SPOT in self.ActiveBuffers[vehicleID]['behavior']:
            transmitted_behavior_list.append(SPOT)


        return transmitted_travel_list, transmitted_behavior_list

    def ClearBuffer(self, vehicleID):
        """
        Empties the buffer lists of a given vehicle

        :param vehicleID: The vehicle whose buffers are to be cleared
        """
        self.ActiveBuffers[vehicleID]['travel'] = []
        self.ActiveBuffers[vehicleID]['behavior'] = []

#-------------------------------------------------------------------------

class CLBuffer:

#-------------------------------------------------------------------------
#Creates the Buffer class. Requires a capacity to start
    def __init__(self, capacity):
        """
        Create dictionary of vehicle IDs

        :param capacity: The capacity of the buffer
        """
        self.ActiveBuffers = {}
        self.TotalCapacity = capacity

    def GetLastRSE(self, vehicleID):
        """
        Returns the last RSE transmitted to by a given vehicle

        :param vehicleID: The vehicle to find the last RSE for
        :return: The last RSE transmitted to by the given vehicle
        """
        return self.ActiveBuffers[vehicleID]['lastRSE']

    #-------------------------------------------------------------------------

    def RemoveSS(self, vehicleID, type, locT, Snapshots, CF):
        """
        Removes Snap Shots from buffer of a given vehicle

        :param vehicleID: The vehicle whose buffer the snapshots are removed from
        :param type: The type of snapshots to remove, 1 for stop, 2 for start, 3 for PDM, 4 for BSM
        :param locT: The time the removal is occurring
        :param Snapshots: The snapshot master list
        :param CF: Dictionary of control file inputs
        """
        if type == 1:
            SS = self.ActiveBuffers[vehicleID]['stop'].pop(0)

        elif type == 2:
            SS = self.ActiveBuffers[vehicleID]['start'].pop(0)

        elif type == 4:
            SS = self.ActiveBuffers[vehicleID]['BSM'].pop(0)

        elif type == 3:
            #FIFO
            if CF.Strategy["SSRetention"] == 1:
                SS = self.ActiveBuffers[vehicleID]['periodic'].pop(0)

            #Every other one
            elif CF.Strategy["SSRetention"] == 2:
                if self.ActiveBuffers[vehicleID]['pointer'] < len(self.ActiveBuffers[vehicleID]['periodic']):
                    SS = self.ActiveBuffers[vehicleID]['periodic'].pop(self.ActiveBuffers[vehicleID]['pointer'])

            #Every other one plus keep first and last IDs
            elif CF.Strategy["SSRetention"] == 3:

                startP = self.ActiveBuffers[vehicleID]['pointer']

                #Do until it breaks
                while 1 == 1:

                    if len(self.ActiveBuffers[vehicleID]['periodic']) != 1:

                        if (self.ActiveBuffers[vehicleID]['pointer'] + 1) >= len(
                                self.ActiveBuffers[vehicleID]['periodic']):
                            perSS = self.ActiveBuffers[vehicleID]['pointer'] - 1
                            nextSS = 0
                        elif (self.ActiveBuffers[vehicleID]['pointer'] - 1) < 0:
                            perSS = len(self.ActiveBuffers[vehicleID]['periodic']) - 1
                            nextSS = self.ActiveBuffers[vehicleID]['pointer'] + 1
                        else:
                            perSS = self.ActiveBuffers[vehicleID]['pointer'] - 1
                            nextSS = self.ActiveBuffers[vehicleID]['pointer'] + 1

                        #check to see if SS is the first of the last of a given ID
                        if (self.ActiveBuffers[vehicleID]['periodic'][self.ActiveBuffers[vehicleID]['pointer']][
                                "num"] == self.ActiveBuffers[vehicleID]['periodic'][perSS]["num"]) \
                            and (self.ActiveBuffers[vehicleID]['periodic']["num"] ==
                                     self.ActiveBuffers[vehicleID]['periodic'][nextSS]["num"]):
                            SS = self.ActiveBuffers[vehicleID]['periodic'].pop(self.ActiveBuffers[vehicleID]['pointer'])
                            break

                        #increase pointer
                        if (self.ActiveBuffers[vehicleID]['pointer'] + 1) < len(
                                self.ActiveBuffers[vehicleID]['periodic']):
                            self.ActiveBuffers[vehicleID]['pointer'] = self.ActiveBuffers[vehicleID]['pointer'] + 1
                        else:
                            self.ActiveBuffers[vehicleID]['pointer'] = 1

                        #if it can not find one and at the end of the list goto odd/even
                        if startP == self.ActiveBuffers[vehicleID]['pointer']:
                            self.ActiveBuffers[vehicleID]['pointer'] = startP
                            SS = self.ActiveBuffers[vehicleID]['periodic'].pop(self.ActiveBuffers[vehicleID]['pointer'])
                            if (self.ActiveBuffers[vehicleID]['pointer'] + 1) < len(
                                    self.ActiveBuffers[vehicleID]['periodic']):
                                self.ActiveBuffers[vehicleID]['pointer'] = self.ActiveBuffers[vehicleID]['pointer'] + 1
                            else:
                                self.ActiveBuffers[vehicleID]['pointer'] = 1 #set to 2nd spot
                                break

                    else:
                        self.ActiveBuffers[vehicleID]['pointer'] = 1
                        SS = self.ActiveBuffers[vehicleID]['periodic'].pop(0)
                        break

            #Every other one plus keep last snapshot
            elif CF.Strategy["SSRetention"] == 4:

                #if halfway through the periodic stack then go back to 2nd location
                if self.ActiveBuffers[vehicleID]['pointer'] > len(self.ActiveBuffers[vehicleID]['periodic']) / 2:
                    self.ActiveBuffers[vehicleID]['pointer'] = 1 #set to 2nd location

                #if more than one record
                if len(self.ActiveBuffers[vehicleID]['periodic']) != 1:

                    #if equal to 1st location set to 2nd to save latest SS
                    if self.ActiveBuffers[vehicleID]['pointer'] == 0:
                        self.ActiveBuffers[vehicleID]['pointer'] = 1

                    #remove snapshot
                    SS = self.ActiveBuffers[vehicleID]['periodic'].pop(self.ActiveBuffers[vehicleID]['pointer'])

                    #increase pointer location
                    if (self.ActiveBuffers[vehicleID]['pointer'] + 1) < len(self.ActiveBuffers[vehicleID]['periodic']):
                        self.ActiveBuffers[vehicleID]['pointer'] = self.ActiveBuffers[vehicleID]['pointer'] + 1
                    else:
                        self.ActiveBuffers[vehicleID]['pointer'] = 1 #set to 2nd spot

                        #if only one record
                else:
                    self.ActiveBuffers[vehicleID]['pointer'] = 1
                    SS = self.ActiveBuffers[vehicleID]['periodic'].pop(0)

        #find the SS in the Master list
        Snapshots[SS["num"] - 1]["deltime"] = locT
        Snapshots[SS["num"] - 1]["delreason"] = 1
        if CF.Control["OutputLevel"] >= 3:
            print 'Snapshot deleted from the buffer at time', locT


    #-------------------------------------------------------------------------
    def DeleteSSinLog(self, SS, locT, reason, Snapshots):
        """
        Add Delete Snap Shots information to log

        :param SS: The snapshot being deleted
        :param locT: The time the snapshot is being deleted
        :param reason: The reason the snapshot is being deleted
        :param Snapshots: The master list of snapshots
        """
        if (SS["VID"] not in self.ActiveBuffers):
            #Add to Active Buffer
            self.ActiveBuffers[SS["VID"]] = {
                'stop': [],
                'start': [],
                'periodic': [],
                'BSM': [],
                'pointer': 0,
                'lastRSE': -1
            }
        Snapshots[SS["num"] - 1]["deltime"] = locT
        Snapshots[SS["num"] - 1]["delreason"] = reason
        Snapshots[SS["num"] - 1]["lastRSE"] = self.GetLastRSE(SS["VID"])

    #-------------------------------------------------------------------------
    def create_buffer(self, v_id):
        """
        Creates a snapshot buffer for the given vehicle
        :param v_id: The vehicle to create a buffer for
        """

        if (v_id not in self.ActiveBuffers):
            #Add to Active Buffer
            self.ActiveBuffers[v_id] = {
                'stop': [],
                'start': [],
                'periodic': [],
                'BSM': [],
                'pointer': 0,
                'lastRSE': -1
            }

    #-------------------------------------------------------------------------
    def AddSS(self, veh_data, SS, locT, Snapshots, CF):

        """
        Add new snapshot to buffer of a given vehicle

        :param veh_data: The vehicle adding the snapshot
        :param SS: The snapshot being added
        :param locT: The time the snapshot is being added
        :param Snapshots: The master list of snapshots
        :param CF: Dictionary of control file inputs
        """
        v_id = veh_data['vehicle_ID']

        #9.2 Manage Buffer Contents
        #Check if vehicle is currently in self.ActiveBuffers
        if (v_id not in self.ActiveBuffers):
            #Add to Active Buffer
            self.ActiveBuffers[v_id] = {
                'stop': [],
                'start': [],
                'periodic': [],
                'BSM': [],
                'pointer': 0,
                'lastRSE': -1
            }
            if SS["type"] == 1:
                self.ActiveBuffers[v_id]['stop'].append(SS)
            elif SS["type"] == 2:
                self.ActiveBuffers[v_id]['start'].append(SS)
            elif SS["type"] == 3:
                self.ActiveBuffers[v_id]['periodic'].append(SS)


        #else, if the buffer is not at full capacity, add the new snapshot
        elif (self.BufferCount(v_id) <= (self.TotalCapacity - 1)):
        #Add SS to correct Buffer
            if SS["type"] == 1:
                self.ActiveBuffers[v_id]['stop'].append(SS)
            elif SS["type"] == 2:
                self.ActiveBuffers[v_id]['start'].append(SS)
            elif SS["type"] == 3:
                self.ActiveBuffers[v_id]['periodic'].append(SS)

        else:
            #If Stop SS
            if SS["type"] == 1:

                #look in Periodic 1st
                if len(self.ActiveBuffers[v_id]['periodic']) > 0:
                    #remove record from Periodic
                    self.RemoveSS(v_id, 3, locT, Snapshots, CF)
                    #add to Stopbuffer
                    self.ActiveBuffers[v_id]['stop'].append(SS)
                #start 2nd
                elif len(self.ActiveBuffers[v_id]['start']) > 0:
                    #remove last record from Starts
                    self.RemoveSS(v_id, 2, locT, Snapshots, CF)
                    #add to Stopbuffer
                    self.ActiveBuffers[v_id]['stop'].append(SS)
                #clear old stop
                elif len(self.ActiveBuffers[v_id]['stop']) > 0:
                    #remove last record from Stops
                    self.RemoveSS(v_id, 1, locT, Snapshots, CF)
                    #add to Stopbuffer
                    self.ActiveBuffers[v_id]['stop'].append(SS)

            #if Start SS
            elif SS["type"] == 2:
                #look in Periodic 1st
                if len(self.ActiveBuffers[v_id]['periodic']) > 0:
                    #remove record from Periodic
                    self.RemoveSS(v_id, 3, locT, Snapshots, CF)
                    #add to Startbuffer
                    self.ActiveBuffers[v_id]['start'].append(SS)
                #remove old start
                elif len(self.ActiveBuffers[v_id]['start']) > 0:
                    #remove last record from Starts
                    self.RemoveSS(v_id, 2, locT, Snapshots, CF)
                    #add to Startbuffer
                    self.ActiveBuffers[v_id]['start'].append(SS)
                else:
                    #just Delete SS
                    self.DeleteSSinLog(SS, locT, 1, Snapshots)

            #if a Periodic SS
            elif SS["type"] == 3:
                if len(self.ActiveBuffers[v_id]['periodic']) > 0:
                    #remove record from Periodic
                    self.RemoveSS(v_id, 3, locT, Snapshots, CF)
                    #add to Periodic
                    self.ActiveBuffers[v_id]['periodic'].append(SS)
                else:
                    #just Delete SS
                    self.DeleteSSinLog(SS, locT, 1, Snapshots)

            elif SS["type"] == 4:
                #FIFO
                self.RemoveSS(v_id, 4, locT, Snapshots, CF)
                #add to BSM
                self.ActiveBuffers[v_id]['BSM'].append(SS)


    #-------------------------------------------------------------------------
    def BufferCount(self, vehicleID):
        """
        Count the number of PDMs in a vehicle's buffer

        :param vehicleID: The vehicle whose buffer length is counted
        :return: The length of the vehicle's buffer
        """

        if vehicleID not in self.ActiveBuffers.keys():
            return 0
        else:
            return len(self.ActiveBuffers[vehicleID]['stop']) + len(self.ActiveBuffers[vehicleID]['start']) \
                   + len(self.ActiveBuffers[vehicleID]['periodic'])


    #------------------------------------------------------------------------
    def ClearBuffer(self, vehicleID, locT, Snapshots, reason, transmitted_to, transTime):
        """
        Clears snapshot buffer of given vehicle

        :param vehicleID: The vehicle whose buffer is cleared
        :param locT: The time the buffer is cleared
        :param Snapshots: Master list of snapshots
        :param reason: The reason the buffer is being cleared
        :param transmitted_to: Where the snapshots are being transmitted to
        :param transTime: The time the snapshots are being transmitted
        """

        for i in self.ActiveBuffers[vehicleID]['stop']:
            Snapshots[i["num"] - 1]["deltime"] = locT
            Snapshots[i["num"] - 1]["delreason"] = reason
            Snapshots[i["num"] - 1]["transTo"] = transmitted_to
            Snapshots[i["num"] - 1]["transtime"] = transTime

        #Clear Start Buffer
        for i in self.ActiveBuffers[vehicleID]['start']:
            Snapshots[i["num"] - 1]["deltime"] = locT
            Snapshots[i["num"] - 1]["delreason"] = reason
            Snapshots[i["num"] - 1]["transTo"] = transmitted_to
            Snapshots[i["num"] - 1]["transtime"] = transTime

        #Clear Periodic Buffer
        for i in self.ActiveBuffers[vehicleID]['periodic']:
            Snapshots[i["num"] - 1]["deltime"] = locT
            Snapshots[i["num"] - 1]["delreason"] = reason
            Snapshots[i["num"] - 1]["transTo"] = transmitted_to
            Snapshots[i["num"] - 1]["transtime"] = transTime


        self.ActiveBuffers[vehicleID]['stop'] = []
        self.ActiveBuffers[vehicleID]['start'] = []
        self.ActiveBuffers[vehicleID]['periodic'] = []
        self.ActiveBuffers[vehicleID]['BSM'] = []
        self.ActiveBuffers[vehicleID]['pointer'] = 0
        self.ActiveBuffers[vehicleID]['lastRSE'] = transmitted_to

    #------------------------------------------------------------------------
    def TransmitPDM(self, veh_data, transTo, isCellular, tp, Snapshots, CF, latency):
        """
        Transmits PDMs in a given vehicles buffer

        :param veh_data: The vehicle transmitting the messages
        :param transTo: The RSE or Cellular Region being transmitted to
        :param isCellular: True if message is being sent via cellular, otherwise false
        :param tp: The time the message is being transmitted
        :param Snapshots: The master list of snapshots
        :param CF: Dictionary of control file inputs
        :param latency: The time between the message being transmitted and being received
        """

        vehicleID  = veh_data['vehicle_ID']

        if isCellular:
            lastRSE = self.ActiveBuffers[vehicleID]['lastRSE']
        else:
            lastRSE = transTo

        if CF.Control["OutputLevel"] >= 3:
            print "Transmitted via %s, Number in buffers: stop:%s,start:%s,Per:%s" % \
                  (transTo,len(self.ActiveBuffers[vehicleID]['stop']), len(self.ActiveBuffers[vehicleID]['start']),
                   len(self.ActiveBuffers[vehicleID]['periodic']))
        #PDM
        # Sort out all the snapshots in the buffer by PSN (aka VID), first stop, then start, and periodic snapshots
        sort_by_PSN = {}
        PSN_list = []
        for ss in self.ActiveBuffers[vehicleID]['stop']:
            PSN = Snapshots[ss["num"] - 1]["PSN"]
            if PSN not in PSN_list:
                sort_by_PSN[PSN] = []
                PSN_list.append(PSN)
            sort_by_PSN[PSN].append(Snapshots[ss["num"] - 1])
        for ss in self.ActiveBuffers[vehicleID]['start']:
            PSN = Snapshots[ss["num"] - 1]["PSN"]
            if PSN not in PSN_list:
                sort_by_PSN[PSN] = []
                PSN_list.append(PSN)
            sort_by_PSN[PSN].append(Snapshots[ss["num"] - 1])
        for ss in self.ActiveBuffers[vehicleID]['periodic']:
            PSN = Snapshots[ss["num"] - 1]["PSN"]
            if PSN not in PSN_list:
                sort_by_PSN[PSN] = []
                PSN_list.append(PSN)
            sort_by_PSN[PSN].append(Snapshots[ss["num"] - 1])

        # Now compose messages, up to 4 snapshots per message, starting a new message with each new PSN
        message_num = 0
        for PSN in PSN_list:
            message_num += 1
            ss_num = 0
            for SS in sort_by_PSN[PSN]:
                ss_num += 1
                if ss_num == 5: #this starts a new message if >4
                    message_num += 1
                    ss_num = 1
                Snapshots[SS["num"] - 1]["transtime"] = tp
                Snapshots[SS["num"] - 1]["transTo"] = transTo
                Snapshots[SS["num"] - 1]["lastRSE"] = self.ActiveBuffers[vehicleID]['lastRSE']
                Snapshots[SS["num"] - 1]["msg_num"] = message_num
                Snapshots[SS["num"] - 1]["ss_num"] = ss_num
                Snapshots[SS["num"] - 1]["transmission_received_time"] = tp + latency


        #clear Buffers
        self.ActiveBuffers[vehicleID]['stop'] = []
        self.ActiveBuffers[vehicleID]['start'] = []
        self.ActiveBuffers[vehicleID]['periodic'] = []
        self.ActiveBuffers[vehicleID]['BSM'] = []
        self.ActiveBuffers[vehicleID]['pointer'] = 0
        self.ActiveBuffers[vehicleID]['lastRSE'] = lastRSE


#*************************************************************************
class BufferContentCheck(unittest.TestCase):
    def setUp(self):
        from TCALoadControl import ControlFiles

        self.CF = ControlFiles()
        self.CF.map_dictionary()

        self.CF.Control['OutputLevel'] = 0

        self.buffer = CLBuffer(30)

        self.entry = {}
        self.entry["TimeOfDay"] = 111
        self.entry["time"] = 4500

        self.Snapshots = []

        self.SS = {}

        #Some hardcoded random numbers...
        self.SS["Tnum"] = 11
        self.SS["num"] = 1
        self.SS["time"] = 111
        self.SS["vehicle_ID"] = 123
        self.SS["PSN"] = 12345
        self.SS["spd"] = 15
        self.SS["localtime"] = 111
        self.SS["x"] = 36
        self.SS["y"] = 42
        self.SS["lastRSE"] = 0
        self.SS["type"] = 1
        self.SS["transtime"] = 15
        self.SS["transTo"] = 15
        self.SS["deltime"] = 0
        self.SS["delreason"] = 0
        self.SS["transmission_received_time"] = -1
        self.Snapshots.append(self.SS)

    def test_add(self):
        self.buffer.AddSS(self.SS, self.SS, self.SS["time"], self.Snapshots, self.CF)
        assert self.buffer.BufferCount(self.SS["vehicle_ID"]) == 1

    def test_remove(self):
        self.buffer.AddSS(self.SS, self.SS, self.SS["time"], self.Snapshots, self.CF)
        assert self.buffer.BufferCount(self.SS["vehicle_ID"]) == 1
        self.buffer.RemoveSS(self.SS["vehicle_ID"], 1, 111, self.Snapshots, self.CF)
        assert self.buffer.BufferCount(self.SS["vehicle_ID"]) == 0

    def test_bufferCount(self):
        self.buffer.AddSS(self.SS, self.SS, self.SS["time"], self.Snapshots, self.CF)
        self.buffer.AddSS(self.SS, self.SS, self.SS["time"], self.Snapshots, self.CF)
        self.buffer.AddSS(self.SS, self.SS, self.SS["time"], self.Snapshots, self.CF)
        assert self.buffer.BufferCount(self.SS["vehicle_ID"]) == 3

    def test_transmit(self):
        self.buffer.AddSS(self.SS, self.SS, self.SS["time"], self.Snapshots, self.CF)
        self.buffer.TransmitPDM(self.SS, False, 0, self.SS["time"], self.Snapshots, self.CF, 0)



if __name__ == '__main__':
    unittest.main()