#standard
import unittest

class CLBuffer:

#-------------------------------------------------------------------------
#Creates the Buffer class. Requires a capacity to start
    def __init__(self, capacity):
        #Create dictionary of vehicle IDs
        self.ActiveBuffers = {}
        self.TotalCapacity = capacity
        self.LastRSE = 0

    def GetLastRSE(self, vehicleID):
        return self.ActiveBuffers[vehicleID]['lastRSE']

#-------------------------------------------------------------------------
#Removes Snap Shots from Buffer
    def RemoveSS(self, vehicleID, type, locT, Snapshots, CF):
        if type == 1:
            SS = self.ActiveBuffers[vehicleID]['stop'].pop(0)

        elif type == 2:
            SS = self.ActiveBuffers[vehicleID]['start'].pop(0)

        elif type == 4:
            SS = self.ActiveBuffers[vehicleID]['BSM'].pop(0)

        elif type == 3:
            #FIFO
            if  CF.Strategy["SSRetention"] == 1:
                SS = self.ActiveBuffers[vehicleID]['periodic'].pop(0)

            #Every other one
            elif  CF.Strategy["SSRetention"] == 2:
                if self.ActiveBuffers[vehicleID]['pointer'] < len(self.ActiveBuffers[vehicleID]['periodic']):
                    SS = self.ActiveBuffers[vehicleID]['periodic'].pop(self.ActiveBuffers[vehicleID]['pointer'])

            #Every other one plus keep first and last IDs
            elif  CF.Strategy["SSRetention"] == 3:

                startP = self.ActiveBuffers[vehicleID]['pointer']

                #Do until it breaks
                while 1 == 1:

                    if len(self.ActiveBuffers[vehicleID]['periodic']) != 1:

                        if (self.ActiveBuffers[vehicleID]['pointer'] + 1) >= len(self.ActiveBuffers[vehicleID]['periodic']):
                            perSS = self.ActiveBuffers[vehicleID]['pointer'] - 1
                            nextSS = 0
                        elif  (self.ActiveBuffers[vehicleID]['pointer'] - 1) < 0:
                            perSS = len(self.ActiveBuffers[vehicleID]['periodic']) - 1
                            nextSS = self.ActiveBuffers[vehicleID]['pointer'] + 1
                        else:
                            perSS = self.ActiveBuffers[vehicleID]['pointer'] - 1
                            nextSS = self.ActiveBuffers[vehicleID]['pointer'] + 1

                        #check to see if SS is the first of the last of a given ID
                        if (self.ActiveBuffers[vehicleID]['periodic'][self.ActiveBuffers[vehicleID]['pointer']]["num"] == self.ActiveBuffers[vehicleID]['periodic'][perSS]["num"]) and \
                                (self.ActiveBuffers[vehicleID]['periodic']["num"] == self.ActiveBuffers[vehicleID]['periodic'][nextSS]["num"]):
                            SS = self.ActiveBuffers[vehicleID]['periodic'].pop(self.ActiveBuffers[vehicleID]['pointer'])
                            break

                        #increase pointer
                        if (self.ActiveBuffers[vehicleID]['pointer'] + 1) < len(self.ActiveBuffers[vehicleID]['periodic']):
                            self.ActiveBuffers[vehicleID]['pointer'] = self.ActiveBuffers[vehicleID]['pointer'] + 1
                        else:
                            self.ActiveBuffers[vehicleID]['pointer'] = 1

                        #if it can not find one and at the end of the list goto odd/even
                        if startP == self.ActiveBuffers[vehicleID]['pointer']:
                            self.ActiveBuffers[vehicleID]['pointer'] = startP
                            SS = self.ActiveBuffers[vehicleID]['periodic'].pop(self.ActiveBuffers[vehicleID]['pointer'])
                            if (self.ActiveBuffers[vehicleID]['pointer'] + 1) < len(self.ActiveBuffers[vehicleID]['periodic']):
                                self.ActiveBuffers[vehicleID]['pointer'] = self.ActiveBuffers[vehicleID]['pointer'] + 1
                            else:
                                self.ActiveBuffers[vehicleID]['pointer'] = 1 #set to 2nd spot
                                break

                    else:
                        self.ActiveBuffers[vehicleID]['pointer'] = 1
                        SS = self.ActiveBuffers[vehicleID]['periodic'].pop(0)
                        break

            #Every other one plus keep last snapshot
            elif  CF.Strategy["SSRetention"] == 4:

                #if halfway through the periodic stack then go back to 2nd location
                if self.ActiveBuffers[vehicleID]['pointer'] > len(self.ActiveBuffers[vehicleID]['periodic'])/2:
                    self.ActiveBuffers[vehicleID]['pointer'] = 1 #set to 2nd location

                #if more than one record
                if len(self.ActiveBuffers[vehicleID]['periodic']) != 1:

                        #if equal to 1st location set to 2nd to save latest SS
                        if self.ActiveBuffers[vehicleID]['pointer'] == 0 :
                            self.ActiveBuffers[vehicleID]['pointer']=1

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
        if CF.Control["OutputLevel"]>= 3:
            print 'Snapshot deleted from the buffer at time',locT

#-------------------------------------------------------------------------
#Add Delete Snap Shots information to log
    def DeleteSSinLog(self, SS, locT, reason, Snapshots):
        #find the SS in the Master list
        Snapshots[SS["num"] - 1]["deltime"] = locT
        Snapshots[SS["num"] - 1]["delreason"] = reason
        Snapshots[SS["num"] - 1]["lastRSE"] = self.ActiveBuffers[SS["Tnum"]]['lastRSE']

#-------------------------------------------------------------------------
#Add new SS to buffer
    def AddSS(self, vehicleID, SS, locT, Snapshots, CF, typeBSM):

#9.2 Manage Buffer Contents
        #Check if vehicle is currently in self.ActiveBuffers
        if(vehicleID not in self.ActiveBuffers):
            #Add to Active Buffer
            self.ActiveBuffers[vehicleID] = {
            'stop' : [],
            'start' : [],
            'periodic' : [],
            'BSM' : [],
            'pointer' : 0,
            'lastRSE' : 0
            }
            if SS["type"] == 1:
                self.ActiveBuffers[vehicleID]['stop'].append(SS)
            elif SS["type"] == 2:
                self.ActiveBuffers[vehicleID]['start'].append(SS)
            elif SS["type"] == 3:
                self.ActiveBuffers[vehicleID]['periodic'].append(SS)
            elif SS["type"] == 4:
                self.ActiveBuffers[vehicleID]['BSM'].append(SS)


        #else, if the buffer is not at full capacity, add the new snapshot
        elif (self.BufferCount(vehicleID, typeBSM) <= (self.TotalCapacity - 1)):
            #Add SS to correct Buffer
                if SS["type"] == 1:
                    self.ActiveBuffers[vehicleID]['stop'].append(SS)
                elif SS["type"] == 2:
                    self.ActiveBuffers[vehicleID]['start'].append(SS)
                elif SS["type"] == 3:
                    self.ActiveBuffers[vehicleID]['periodic'].append(SS)
                elif SS["type"] == 4:
                    self.ActiveBuffers[vehicleID]['BSM'].append(SS)

            #else remove a previous SS, then add the new one
        else:
            #If Stop SS
            if SS["type"] == 1:

                #look in Periodic 1st
                if len(self.ActiveBuffers[vehicleID]['periodic']) > 0:
                    #remove record from Periodic
                    self.RemoveSS(vehicleID, 3, locT, Snapshots, CF)
                    #add to Stopbuffer
                    self.ActiveBuffers[vehicleID]['stop'].append(SS)
                #start 2nd
                elif len(self.ActiveBuffers[vehicleID]['start']) > 0:
                    #remove last record from Starts
                    self.RemoveSS(vehicleID, 2, locT, Snapshots, CF)
                    #add to Stopbuffer
                    self.ActiveBuffers[vehicleID]['stop'].append(SS)
                #clear old stop
                elif len(self.ActiveBuffers[vehicleID]['stop']) > 0:
                    #remove last record from Stops
                    self.RemoveSS(vehicleID, 1, locT, Snapshots, CF)
                    #add to Stopbuffer
                    self.ActiveBuffers[vehicleID]['stop'].append(SS)

            #if Start SS
            elif SS["type"] == 2:
                #look in Periodic 1st
                if len(self.ActiveBuffers[vehicleID]['periodic']) > 0:
                    #remove record from Periodic
                    self.RemoveSS(vehicleID, 3, locT, Snapshots, CF)
                    #add to Startbuffer
                    self.ActiveBuffers[vehicleID]['start'].append(SS)
                #remove old start
                elif len(self.ActiveBuffers[vehicleID]['start']) > 0:
                    #remove last record from Starts
                    self.RemoveSS(vehicleID, 2, locT, Snapshots, CF)
                    #add to Startbuffer
                    self.ActiveBuffers[vehicleID]['start'].append(SS)
                else:
                    #just Delete SS
                    self.DeleteSSinLog(SS, locT, 1, Snapshots)

            #if a Periodic SS
            elif SS["type"] == 3:
                if len(self.ActiveBuffers[vehicleID]['periodic']) > 0:
                    #remove record from Periodic
                    self.RemoveSS(vehicleID, 3, locT, Snapshots, CF)
                    #add to Periodic
                    self.ActiveBuffers[vehicleID]['periodic'].append(SS)
                else:
                    #just Delete SS
                    self.DeleteSSinLog(SS, locT, 1, Snapshots)

            elif SS["type"] == 4:
                #FIFO
                self.RemoveSS(vehicleID, 4, locT, Snapshots, CF)
                #add to BSM
                self.ActiveBuffers[vehicleID]['BSM'].append(SS)

#-------------------------------------------------------------------------
#Print snapshot record
    def PrintSS(self, SS):
         print "%s,%d,%d,%s,%s,%s,%s,%s,%s,%d" % (
           SS["time"], int(SS["x"]), int(SS["y"]), SS["spd"], SS["VID"],
           SS["type"], SS["transtime"], SS["transRSE"], SS["deltime"], SS["transmission_received_time"])

#-------------------------------------------------------------------------
#prints all buffer SS
    def PrintBuffer(self,vehicleID):    # Currently this is not called anywhere, but could be for debugging
        print 'Stop snapshots: '
        for i in self.ActiveBuffers[vehicleID]['stop']:
            self.PrintSS(i)

        print 'Start Snapshots: '
        for i in self.ActiveBuffers[vehicleID]['start']:
            self.PrintSS(i)

        print 'Periodic snapshots: '
        for i in self.ActiveBuffers[vehicleID]['periodic']:
            self.PrintSS(i)

#-------------------------------------------------------------------------
#find Buffer count
    def BufferCount(self, vehicleID, typeBSM):
        #Count the number of snapshots or BSM in a vehicle's buffer
        if vehicleID not in self.ActiveBuffers.keys():
            return 0
        elif typeBSM:
            return len(self.ActiveBuffers[vehicleID]['BSM'])
        else:
            return len(self.ActiveBuffers[vehicleID]['stop']) + len(self.ActiveBuffers[vehicleID]['start']) \
                   + len(self.ActiveBuffers[vehicleID]['periodic'])


#------------------------------------------------------------------------
    def ClearBuffer(self, vehicleID, locT, Snapshots, reason, RSE, transTime):

        #Clear stop Buffer
        for i in self.ActiveBuffers[vehicleID]['stop']:
            Snapshots[i["num"] - 1]["deltime"] = locT
            Snapshots[i["num"] - 1]["delreason"] = reason
            Snapshots[i["num"] - 1]["transRSE"] = RSE
            Snapshots[i["num"] - 1]["transtime"] = transTime

        #Clear Start Buffer
        for i in self.ActiveBuffers[vehicleID]['start']:
            Snapshots[i["num"] - 1]["deltime"] = locT
            Snapshots[i["num"] - 1]["delreason"] = reason
            Snapshots[i["num"] - 1]["transRSE"] = RSE
            Snapshots[i["num"] - 1]["transtime"] = transTime

        #Clear Periodic Buffer
        for i in self.ActiveBuffers[vehicleID]['periodic']:
            Snapshots[i["num"] - 1]["deltime"] = locT
            Snapshots[i["num"] - 1]["delreason"] = reason
            Snapshots[i["num"] - 1]["transRSE"] = RSE
            Snapshots[i["num"] - 1]["transtime"] = transTime

        #Clear BSM Buffer
        for i in self.ActiveBuffers[vehicleID]['BSM']:
            Snapshots[i["num"] - 1]["deltime"] = locT
            Snapshots[i["num"] - 1]["delreason"] = reason
            Snapshots[i["num"] - 1]["transRSE"] = RSE
            Snapshots[i["num"] - 1]["transtime"] = transTime

        self.ActiveBuffers[vehicleID]['stop'] = []
        self.ActiveBuffers[vehicleID]['start'] = []
        self.ActiveBuffers[vehicleID]['periodic'] = []
        self.ActiveBuffers[vehicleID]['BSM'] = []
        self.ActiveBuffers[vehicleID]['pointer'] = 0
        self.ActiveBuffers[vehicleID]['lastRSE'] = RSE

#-------------------------------------------------------------------------
    def TransmitBSM(self, vehicleID, RSE, entry, BSMs, CF):

        if CF.Debugger >= 2:
            print "Transmit to RSE %s Number in buffer: BSM:%s" % (RSE, len.ActiveBuffers[vehicleID]['BSM'])

        #Compose messages, up to 4 BSMs per message
        message_num = 1
        ss_num = 0
        for BSM in self.ActiveBuffers[vehicleID]['BSM']:
            ss_num += 1
            if ss_num == 5: #this starts a new message if >4
                message_num += 1
                ss_num = 1
            BSMs[BSM["num"] - 1]["msg_num"] = message_num
            BSMs[BSM["num"] - 1]["ss_num"] = ss_num

        self.ActiveBuffers[vehicleID]['BSM'] = []


#-------------------------------------------------------------------------
#prints all buffer SS
    def Transmit(self, vehicleID, RSE, entry, Snapshots, CF, latency, typeBSM):
#10.0

        if CF.Control["OutputLevel"] >= 2:
            print "Transmit to RSE %s Number in buffers: stop:%s,start:%s,Per:%s,BSM:%s" % (RSE,
                len(self.ActiveBuffers[vehicleID]['stop']),len(self.ActiveBuffers[vehicleID]['start']),
                len(self.ActiveBuffers[vehicleID]['periodic']),len(self.ActiveBuffers[vehicleID]['BSM']))

        #PDM
        # Sort out all the snapshots in the buffer by PSN (aka VID), first stop, then start, and periodic snapshots
        if not typeBSM:
            sort_by_PSN = {}
            PSN_list = []
            for ss in self.ActiveBuffers[vehicleID]['stop']:
                PSN = Snapshots[ss["num"]-1]["VID"]
                if PSN not in PSN_list:
                    sort_by_PSN[PSN] = []
                    PSN_list.append(PSN)
                sort_by_PSN[PSN].append(Snapshots[ss["num"]-1])
            for ss in self.ActiveBuffers[vehicleID]['start']:
                PSN = Snapshots[ss["num"]-1]["VID"]
                if PSN not in PSN_list:
                    sort_by_PSN[PSN] = []
                    PSN_list.append(PSN)
                sort_by_PSN[PSN].append(Snapshots[ss["num"]-1])
            for ss in self.ActiveBuffers[vehicleID]['periodic']:
                PSN = Snapshots[ss["num"]-1]["VID"]
                if PSN not in PSN_list:
                    sort_by_PSN[PSN] = []
                    PSN_list.append(PSN)
                sort_by_PSN[PSN].append(Snapshots[ss["num"]-1])

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
                    Snapshots[SS["num"] - 1]["transtime"] = entry["time"]
                    Snapshots[SS["num"] - 1]["transRSE"] = RSE
                    Snapshots[SS["num"] - 1]["lastRSE"] = self.ActiveBuffers[vehicleID]['lastRSE']
                    Snapshots[SS["num"] - 1]["msg_num"] = message_num
                    Snapshots[SS["num"] - 1]["ss_num"] = ss_num
                    Snapshots[SS["num"] - 1]["transmission_received_time"] = entry["time"] + latency #latency is 0 if transmitted via RSE

            #BSM
        else:
            #Compose messages, up to 4 BSMs per message
            message_num = 1
            ss_num = 0
            for SS in self.ActiveBuffers[vehicleID]['BSM']:
                ss_num += 1
                if ss_num == 5: #this starts a new message if >4
                    message_num += 1
                    ss_num = 1
                Snapshots[SS["num"] - 1]["transtime"] = entry["time"]
                Snapshots[SS["num"] - 1]["transRSE"] = RSE
                Snapshots[SS["num"] - 1]["lastRSE"] = self.ActiveBuffers[vehicleID]['lastRSE']
                Snapshots[SS["num"] - 1]["msg_num"] = message_num
                Snapshots[SS["num"] - 1]["ss_num"] = ss_num
                Snapshots[SS["num"] - 1]["transmission_received_time"] = entry["time"] + latency #latency is 0 if transmitted via RSE

        #clear Buffers
        self.ActiveBuffers[vehicleID]['stop'] = []
        self.ActiveBuffers[vehicleID]['start'] = []
        self.ActiveBuffers[vehicleID]['periodic'] = []
        self.ActiveBuffers[vehicleID]['BSM'] = []
        self.ActiveBuffers[vehicleID]['pointer'] = 0
        self.ActiveBuffers[vehicleID]['lastRSE'] = RSE

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

        self.SS={}

        #Some hardcoded random numbers...
        self.SS["Tnum"] = 11
        self.SS["num"] = 1
        self.SS["time"] = 111
        self.SS["VID"] = 123
        self.SS["spd"] = 15
        self.SS["localtime"] = 111
        self.SS["x"] = 36
        self.SS["y"] = 42
        self.SS["lastRSE"] = 0
        self.SS["type"] = 1
        self.SS["transtime"] = 15
        self.SS["transRSE"] = 15
        self.SS["deltime"] = 0
        self.SS["delreason"] = 0
        self.SS["transmission_received_time"] = -1
        self.Snapshots.append(self.SS)

    def test_add(self):
        self.buffer.AddSS(self.SS["VID"] , self.SS, self.SS["time"], self.Snapshots, self.CF, False)
        assert  self.buffer.BufferCount(self.SS["VID"], False) == 1

    def test_remove(self):
        self.buffer.AddSS(self.SS["VID"], self.SS,self.SS["time"], self.Snapshots, self.CF, False)
        assert  self.buffer.BufferCount(self.SS["VID"], False) == 1
        self.buffer.RemoveSS(self.SS["VID"], 1, 111, self.Snapshots, self.CF)
        assert  self.buffer.BufferCount(self.SS["VID"], False) ==  0

    def test_bufferCount(self):
        self.buffer.AddSS(self.SS["VID"],self.SS, self.SS["time"], self.Snapshots, self.CF, False)
        self.buffer.AddSS(self.SS["VID"],self.SS, self.SS["time"], self.Snapshots, self.CF, False)
        self.buffer.AddSS(self.SS["VID"],self.SS, self.SS["time"], self.Snapshots, self.CF, False)
        assert self.buffer.BufferCount(self.SS["VID"], False) == 3

    def test_transmit(self):
        self.buffer.AddSS(self.SS["VID"],self.SS, self.SS["time"], self.Snapshots, self.CF, False)
        self.buffer.Transmit(self.SS["VID"], 0, self.entry, self.Snapshots, self.CF, 0, False)

    def test_add_BSM(self):
        self.SS["type"] = 4
        self.buffer.AddSS(self.SS["VID"], self.SS, self.SS["time"], self.Snapshots, self.CF, True)
        assert self.buffer.BufferCount(self.SS["VID"], True) == 1



if __name__ == '__main__':
    unittest.main()