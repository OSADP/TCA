#Standard
import unittest
import os

#external
import pandas as pd

#TCA
from TCABuffer import CLBuffer, SPOTBuffer
from TCACore import  logger, Timer, Get_Heading_Change, SPOT_time
from TCADataStore import DataStorage
from TCARandom import Random_generator
from TCABSM import BSM
from TCACAM import CAM
from TCASPOT import SPOT
from TCAPDM import PDM
from TCABMM import BMM


class TCA_Algorithm:
    def __init__(self, CF, RSEs, RSE_tree, RandomGen_seed, Regions, SPOT_tree, msg_limit = 800000, link_included = False):

        """
        Initializes TCA_Algorithm module

        :param CF: Dictionary of Control File defined attributes
        :param RSEs: List of RSEs
        :param RSE_tree: Location tree of RSEs
        :param RandomGen: Seed value for randomization
        :param Regions: Regions class
        :param SPOT_tree: Location tree of SPOT devices
        :param msg_limit: Limit of snapshot list before outputting to a file
        """

        self.RSEs = RSEs
        self.RSE_tree = RSE_tree
        self.CF = CF
        self.regions = Regions

        self.random_generator = Random_generator(RandomGen_seed)

        self.random_generator.add_generator_int('LossPercent', 1, 100)
        self.random_generator.add_generator_int('TypePercent', 1, 100)

        self.BSM = BSM(self.random_generator.generate_seed(), self.CF, self.regions)
        self.CAM = CAM(self.random_generator.generate_seed(), self.CF)
        self.SPOT = SPOT(self.random_generator.generate_seed(), self.CF, SPOT_tree)
        self.PDM = PDM(self.random_generator.generate_seed(), self.CF, RSE_tree, self.regions)
        self.BMM = BMM(self.random_generator.generate_seed(), self.CF, self.regions)


        self.msgs = {'BSM': self.BSM, 'CAM': self.CAM, 'SPOT': self.SPOT, 'PDM': self.PDM, 'BMM': self.BMM}

        self.tbl = DataStorage(self.random_generator, link_included = link_included)

        #Each Vehicle RSE list
        self.VehicleRSE = {}

        #Limit of message list before printing to a file
        self.msg_limit = msg_limit

        self.BMMPrintTimes = {}
        self.CountsUpdated = {}
        if self.BMM.Triggers is not None:
            for trigger in self.BMM.Triggers.triggers:
                self.BMMPrintTimes[self.BMM.Triggers.triggers[trigger].title] = 0
                self.CountsUpdated[self.BMM.Triggers.triggers[trigger].title] = -1
        
        #BMM Count by type
        self.BMMCounts = {}

        #BMM Count by link
        self.BMM_Count_By_Link = {}
        
        #BMM Count by Queue Region
        self.BMM_Queue_Region_Count = {}

        #BMM Count by Intersection
        self.BMM_Intersection_Count = {}

        ####
        self.turning_bmms = {}

        #All link_x values where BMM's were generated
        self.BMM_Queue_X = {}



        try:
            if self.BMM.Triggers.link_lengths is not None:
                for link in self.BMM.Triggers.link_lengths:
                    self.BMM_Count_By_Link[link] = 0
        except:
            self.BMM_Count_By_Link = {}
#-------------------------------------------------------------------------           

    def pull_veh_data(self, veh, tp):
        """
        Returns vehicle data for specified time period.

        :param veh: The vehicle id for information to be retrieved
        :param tp: The time in seconds for information to be retrieved
        :return: The vehicle record for the vehicle at the specified time
        """

        vehicle_data = []

        for v in veh:
            vehicle_data.append(self.tbl.pull_veh_data(veh = v, CF = self.CF, RandomGen = self.random_generator, Regions = self.regions, tp = tp, msgs = self.msgs))
        return vehicle_data

    #-------------------------------------------------------------------------
    def CheckCellular(self, veh_data, tp):
        """
        Checks to see if a PDM, BSM, BMM message can be sent via cellular for the given vehicle
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
            

        # ALGORITHM Step 9.4.6.1 BSM Cellular Transmission Process
        if veh_data['BSM_equipped'] and (veh_data['dsrc_transmit_bsm'] == False) and veh_data['cellular_enabled']:
            if float(self.CF.Strategy['BSMFrequencyCellular']) > 0.0:
                if veh_data['prev_time_BSM_cellular_transmit'] + float(self.CF.Strategy['BSMFrequencyCellular']) <= tp:
                    if self.random_generator['LossPercent'] > loss_percent:
                        self.BSM.GenerateTransmit(veh_data=veh_data,
                                        transTo = region_name,
                                        isCellular= True,
                                        isRSE = False)
                        veh_data['prev_time_BSM_cellular_transmit'] = tp

            else:
                if self.random_generator['LossPercent'] > loss_percent:
                    self.BSM.GenerateTransmit(veh_data=veh_data,
                                        transTo = region_name,
                                        isCellular= True,
                                        isRSE = False)


        # ALGORITHM Step 9.4.6.2 PDM Cellular Transmission Process
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
                    logger.debug('Checking for minimum number of SS to transmit')

                #If PDM buffer has the minimum number of snapshots
                if (self.PDM.PDMBuffer.BufferCount(veh_data['vehicle_ID']) >= mintransmit_PDM):
                    if veh_data["time"] != 0:

                        #By random number generator, determine if snapshot transmission is successful. Else delete snapshots.
                        if self.random_generator['LossPercent'] > loss_percent:

                            if self.CF.Control["OutputLevel"] >= 2:
                                 logger.debug("%s SS transmitted at time %d via cellular from vehicle ID: %s" % \
                                       (self.PDM.PDMBuffer.BufferCount(veh_data['vehicle_ID']), veh_data["time"], veh_data['vehicle_ID']))

                            self.PDM.PDMBuffer.TransmitPDM(veh_data=veh_data,
                                                       transTo=region_name,
                                                       isCellular=True,
                                                       tp = veh_data["time"],
                                                       Snapshots=self.PDM.PDM_list,
                                                       latency=latency,
                                                       CF=self.CF)

                        else:
                            #Delete reason 5: transmission lost
                            self.PDM.PDMBuffer.ClearBuffer(vehicleID = veh_data['vehicle_ID'],
                                                        locT = veh_data["time"],
                                                        Snapshots = self.PDM.PDM_list,
                                                        reason = 5,
                                                        transmitted_to = -1,
                                                        transTime = veh_data["time"])

                        veh_data['prev_time_PDM_cellular_transmit']= veh_data["time"]

        # ALGORITHM Step 9.4.6.3 BMM Cellular Transmission Process
        if veh_data['DIDC_equipped']:
            
            if self.BMM.BMMBuffer.GetBufferSize(veh_data['vehicle_ID']) >= self.BMM.DIDC['BMMTransmissionThreshold']:
                if self.CF.Control["OutputLevel"] >= 2:
                    logger.debug("BMM Transmission via cellular for vehicle ID: %s at time: %s with %s BMMs in the buffer" %
                                (veh_data['vehicle_ID'], veh_data['time'], self.BMM.BMMBuffer.GetBufferSize(veh_data['vehicle_ID'])))
                new_bmms = self.BMM.BMMBuffer.Transmit(veh_data['vehicle_ID'],veh_data['time'])
                self.BMM.BMM_list.extend(new_bmms)
                self.countTransmittedBMMs(new_bmms)

        # ALGORITHM Step 9.4.6.4 CAM Cellular Transmission Process
        if veh_data['CAM_equipped']:
            if self.CAM.CheckMessage(veh_data, tp):
                #Check if vehicle is within a defined cellular region
                if self.regions is not None:
                    for region in self.regions.cell_regions:
                        if region.in_region(veh_data['location_x'], veh_data['location_y']):
                            #Assign the defined regions loss percentage 
                            loss_percent = float(region.loss)
                            region_name = region.title
                            break
                if self.random_generator['LossPercent'] > loss_percent:
                    if self.CF.Control['OutputLevel'] >= 2:
                        logger.debug('Time: %s Vehicle ID: %s - Transmitting CAM via cellular' % (tp,veh_data['vehicle_ID']))
                    self.CAM.GenerateTransmit(veh_data=veh_data,
                                             transTo = 'cellular',
                                             tp = tp)

#-------------------------------------------------------------------------
    def CheckDSRC(self, veh_data, tp, range_data):
        """
        Checks to see if a PDM, BSM or CAM message can be sent via DSRC for the given vehicle
        in the given time

        :param veh_data: The vehicle to check
        :param tp: The time period to check in
        """

        #Select vehicles that are active and DSRC enabled (exclusively or dual)
        if ((tp % 1 ==0) and (veh_data['PDM_equipped']) and (veh_data['in_privacy_gap'] == False)) \
            or (veh_data['BSM_equipped']) or (veh_data['CAM_equipped']) or (veh_data['DIDC_equipped']):


            transmit_BSM = False
            transmit_PDM = False

            if len(range_data[veh_data['vehicle_ID']]) > 0:
                if veh_data['BSM_equipped']:
                    if (float(veh_data['prev_time_BSM_dsrc_transmit']) + float(self.CF.Strategy['BSMFrequencyDSRC'])) <= tp:
                        transmit_BSM = True

                if (tp % 1 ==0) and veh_data['PDM_equipped']:
                    if (float(veh_data['prev_time_PDM_dsrc_transmit']) + float(self.CF.Strategy['PDMFrequencyDSRC'])) <= tp:
                        transmit_PDM = True


            for roadside_equipment in range_data[veh_data['vehicle_ID']]:
                if self.CF.Control["OutputLevel"] >= 3:
                    logger.debug('Time: %s Vehicle ID: %s - Checking RSE: %s' % (tp,veh_data['vehicle_ID'], roadside_equipment))

                if veh_data['BSM_equipped'] and transmit_BSM:
                    if self.random_generator['LossPercent'] > self.RSEs.RSEList[roadside_equipment]['loss_rate']:
                        self.BSM.GenerateTransmit(veh_data=veh_data,
                                                 transTo = roadside_equipment,
                                                 isCellular= False,
                                                 isRSE = True)
                        veh_data['dsrc_transmit_bsm'] = True
                        veh_data['prev_time_BSM_dsrc_transmit'] = tp


                if transmit_PDM and (veh_data['vehicle_ID'] in self.PDM.PDMBuffer.ActiveBuffers.keys()) > 0:
                    if self.PDM.PDMBuffer.BufferCount(veh_data['vehicle_ID']) >= self.CF.Strategy['MinNumberofPDMtoTransmitViaDSRC']:
                        if self.random_generator['LossPercent'] > self.RSEs.RSEList[roadside_equipment]['loss_rate']:
                            veh_data['dsrc_transmit_pdm'] = True
                            veh_data['prev_time_PDM_dsrc_transmit'] = tp
                            self.RSETransmitPDM(veh_data, roadside_equipment)
                        else:
                            #Delete reason 5: transmission lost
                            self.PDM.PDMBuffer.ClearBuffer(vehicleID = veh_data['vehicle_ID'],
                                                        locT = tp,
                                                        Snapshots = self.PDMs,
                                                        reason = 5,
                                                        transmitted_to = -1,
                                                        transTime = -1)

                if veh_data['CAM_equipped']:
                    if self.CAM.CheckMessage(veh_data, tp):
                        if self.random_generator['LossPercent'] > self.RSEs.RSEList[roadside_equipment]['loss_rate']:
                            if self.CF.Control['OutputLevel'] >= 2:
                                logger.debug('Time: %s Vehicle ID: %s - Transmitting CAM to RSE: %s' % (tp,veh_data['vehicle_ID'], roadside_equipment))
                            self.CAM.GenerateTransmit(veh_data=veh_data,
                                                     transTo = roadside_equipment,
                                                     tp = tp)

                if veh_data['DIDC_equipped']:                   
                    if self.BMM.BMMBuffer.GetBufferSize(veh_data['vehicle_ID']) >= self.BMM.DIDC['BMMTransmissionThreshold']:
                        if self.CF.Control["OutputLevel"] >= 2:
                            logger.debug("BMM Transmission via RSE ID %s for vehicle ID: %s at time: %s with %s BMMs in the buffer" %
                                        (roadside_equipment, veh_data['vehicle_ID'], veh_data['time'], self.BMM.BMMBuffer.GetBufferSize(veh_data['vehicle_ID'])))
                        new_bmms = self.BMM.BMMBuffer.Transmit(veh_data['vehicle_ID'],veh_data['time'], roadside_equipment)
                        self.BMM.BMM_list.extend(new_bmms)
                        self.countTransmittedBMMs(new_bmms)




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
                    (self.PDM.PDMBuffer.BufferCount(veh_data['vehicle_ID']), veh_data["time"], RSE, veh_data['vehicle_ID']))

            self.PDM.PDMBuffer.TransmitPDM(veh_data=veh_data,
                                       transTo=RSE,
                                       isCellular=False,
                                       tp = veh_data['time'],
                                       Snapshots=self.PDM.PDM_list,
                                       CF=self.CF,
                                       latency= self.RSEs.RSEList[RSE]['latency'])


    #-------------------------------------------------------------------------
    def CheckDIDC(self, veh_data, tp):
        for trigger in self.BMM.Triggers.triggers:
            if 'Burst' not in self.BMM.Triggers.triggers[trigger].title:
                if self.BMMPrintTimes[self.BMM.Triggers.triggers[trigger].title] == 0:
                    self.BMMPrintTimes[self.BMM.Triggers.triggers[trigger].title] = tp + self.BMM.Triggers.triggers[trigger].OptimizationInterval
                if tp >= self.BMMPrintTimes[self.BMM.Triggers.triggers[trigger].title] and tp != self.CountsUpdated[self.BMM.Triggers.triggers[trigger].title]:
                    self.processTimeInterval(tp, trigger)
       
        self.BMM.Check(veh_data, tp)
    #-------------------------------------------------------------------------
    def processTimeInterval(self, tp, trigger):
        """Counts and prints out the totals of all types of BMMs at the end of each interval
        :param tp: time
        """

        if self.CF.Control['OutputLevel'] >=2:
            template = "{0:30}|{1:>10}|{2:>10}|"
            line = '-'*100
            logger.info('\nTime Interval %s - %s Trigger: %s \n%s\nDIDC' % (tp- self.BMM.Triggers.triggers[trigger].OptimizationInterval, tp, self.BMM.Triggers.triggers[trigger].title, line) )
            logger.info( template.format('','BMM Count:','Size:') )
            #Print out counts by bmm type
            for k,v in self.BMMCounts.iteritems():
                if v > 0:
                    logger.info( template.format(self.BMM.BMM_Type[k], v, v*self.BMM.DIDC['MessageSize']) ) 

        #=======================
        self.BMM.event_count = {}
        self.BMM.turning_event_count = {}
        #=======================

        #DIDC Adjustments 
        if 'Periodic' == trigger and (self.BMM.Triggers.triggers['Periodic'].TargetBMMsPerSegment or self.BMM.Triggers.triggers['Periodic'].TargetSamplingRate):
            self.checkPeriodicSamplingRates(tp)
            if len(self.BMM_Count_By_Link) > 0:
                for link in self.BMM_Count_By_Link.keys():
                    self.BMM_Count_By_Link[link] = 0
        if 'Queue' == trigger and self.BMM.Triggers.triggers['Queue'].queue_estimation:
            self.checkQueueSamplingRates()
            self.BMM_Queue_Region_Count = {}
            self.BMM_Queue_X= {}
        if 'Turning' == trigger and self.BMM.Triggers.triggers['Turning'].TargetBMMsPerIntersection:
            self.checkTurningSamplingRates()
            #==============================
            self.turning_bmms = {}
            #===============================
            if len(self.BMM_Intersection_Count) > 0:
                self.BMM_Intersection_Count = {}
        if 'Traction Control' == trigger:
            self.checkTractionControl(tp)
            for burst_trigger in self.BMM.burst_extensions.keys():
                info = self.BMM.burst_extensions[burst_trigger]
                if info[2] < tp:
                    self.BMM.burst_extensions.pop(burst_trigger)

        self.BMMCounts[trigger] = 0
            
        self.CountsUpdated[self.BMM.Triggers.triggers[trigger].title] = tp
        self.BMMPrintTimes[self.BMM.Triggers.triggers[trigger].title] = tp + self.BMM.Triggers.triggers[trigger].OptimizationInterval

    #-------------------------------------------------------------------------           

    def countTransmittedBMMs(self, new_bmms):
        """Counts BMMs by type as they are being transmitted
        :param new_bmms: list of bmms that were just transmitted
        """          
        Triggers = self.BMM.Triggers.triggers
    
        for BMM in new_bmms:
            # Count by type
            if BMM['BMM_Type'] in self.BMMCounts:
                self.BMMCounts[BMM['BMM_Type']] +=1
            else:
                self.BMMCounts[BMM['BMM_Type']] = 1

            if len(self.BMM_Count_By_Link) > 0:
                #Count by link
                if BMM['link'] in self.BMM_Count_By_Link.keys():
                    self.BMM_Count_By_Link[BMM['link']] +=1

            #For Queue Estimation
            #Counts all BMMs in the region for sampling rate targets
            if 'Queue' in Triggers.keys() and Triggers['Queue'].queue_estimation:
                if Triggers['Queue'].in_queue_region(BMM['link'],BMM['link_x']):
                    if BMM['link'] in self.BMM_Queue_Region_Count:
                        self.BMM_Queue_Region_Count[BMM['link']]+=1
                    else:
                        self.BMM_Queue_Region_Count[BMM['link']]= 1

                #Finds all Queue BMMs on the link and their distance to the stop bar to find new queue region
                if BMM['BMM_Type'] == Triggers['Queue'].BMM_Type and BMM['link'] in Triggers['Queue'].queue_estimation.keys():
                        dist = Triggers['Queue'].queue_estimation[BMM['link']]['link_length'] - BMM['link_x']
                        if BMM['link'] in self.BMM_Queue_X.keys():
                            self.BMM_Queue_X[BMM['link']].append(dist)
                        else:
                            self.BMM_Queue_X[BMM['link']] = [dist]
            
            #For Turning Estimation
            #Counts all BMMs in the intersection areas
            if 'Turning' in Triggers.keys() and Triggers['Turning'].intersections != None:
                intersection = Triggers['Turning'].in_intersection(BMM['x'], BMM['y'])
                if intersection:
                    if intersection in self.BMM_Intersection_Count.keys():
                        self.BMM_Intersection_Count[intersection] +=1
                    else:
                        self.BMM_Intersection_Count[intersection] = 1
		              
                    if BMM['BMM_Type'] == Triggers['Turning'].BMM_Type:
                        if intersection in self.turning_bmms.keys():
                            self.turning_bmms[intersection]  += 1
                        else:
                            self.turning_bmms[intersection] = 1

			

    
    #-------------------------------------------------------------------------           
    def checkPeriodicSamplingRates(self, tp):
        """Checks to see if message sampling rates are close to travel time targets and changes generation times if not
        """
        curdir = os.path.dirname(os.path.realpath(__file__)) + os.sep
        gmt_file = curdir + self.CF.Control['PeriodicGMTFile']

        #Target sampling rates (global)
        periodic_template = '\t{0:8}|{1:8}|{2:15}|{3:15}|{4:15}|'        
        periodic_trigger = self.BMM.Triggers.triggers['Periodic']
        bmm_count = sum(self.BMMCounts.values())
        
        if self.CF.Control['OutputLevel'] >=2:        
            logger.info('\nPeriodic\n' + periodic_template.format('Link', 'BMMs:', 'Target BMMs:', 'Current Lambda:', 'New Lambda:') )

        if periodic_trigger.TargetSamplingRate != None:
            k = 1
            new_generation_time = ''

            if bmm_count < 0.95* periodic_trigger.TargetSamplingRate:
                k = 0.9
            elif bmm_count > 1.05* periodic_trigger.TargetSamplingRate:
                k = 1.1
                
            if k != 1:
                periodic_trigger.GenerationMeanTime[-1] *= k
                self.BMM.recreateRandomGenerator(periodic_trigger)

                new_generation_time = periodic_trigger.GenerationMeanTime[-1]
                with open(gmt_file, 'a') as f_out:
                    f_out.write('%s,%s\n' % (tp, new_generation_time))


            if self.CF.Control['OutputLevel'] >= 2:
                logger.info(periodic_template.format('global', bmm_count, periodic_trigger.TargetSamplingRate, periodic_trigger.GenerationMeanTime[-1]/k, new_generation_time))

        
        #Link based targets
        elif periodic_trigger.TargetBMMsPerSegment != None:
            LOW = False
            
            for link in periodic_trigger.links:
                new_generation_time = ''
                region = link
                target_link_BMMs = int(periodic_trigger.TargetBMMsPerSegment * (self.BMM.Triggers.link_lengths[link] / periodic_trigger.SegmentLength)) 

                k = 1
                if not LOW:
                    if self.BMM_Count_By_Link[link] < int(target_link_BMMs*0.9):
                        k = 0.9
                    elif self.BMM_Count_By_Link[link] > int(target_link_BMMs*1.1) and periodic_trigger.region_based_generation:
                        k = 1.1
                
                if not periodic_trigger.region_based_generation:
                    region = -1
                
                if k != 1:
                    periodic_trigger.GenerationMeanTime[region] *= k
                    self.BMM.recreateRandomGenerator(periodic_trigger, region)

                    new_generation_time = periodic_trigger.GenerationMeanTime[region]

                    if not periodic_trigger.region_based_generation:
                        LOW = True

                if self.CF.Control['OutputLevel'] >= 2:
                    logger.info( periodic_template.format(link, self.BMM_Count_By_Link[link], target_link_BMMs, periodic_trigger.GenerationMeanTime[region]/k, new_generation_time))

#-------------------------------------------------------------------------           
    
    def checkQueueSamplingRates(self):
        """Checks to see if message sampling rates are close to queue targets and changes generation times if not
        """
        queue_trigger = self.BMM.Triggers.triggers['Queue']
        if queue_trigger.queue_estimation != None:                
                
                new_regions = self.checkQueueRegion()

                if self.CF.Control['OutputLevel'] >= 2:
                    queue_template = '\t{0:8}|{1:8}|{2:15}|{3:15}|{4:15}|{5:15}|{6:15}|'
                    logger.info( '\nQueue\n' + queue_template.format('Link:','BMMs:','Target BMMs:','Current Region:','New Region:', 'Current Lambda:', 'New Lambda:') )

                for link in queue_trigger.queue_estimation.keys():
                    current_region = queue_trigger.queue_estimation[link]['queue_region_length'] 
                    queue_trigger.queue_estimation[link]['queue_region_length'] = new_regions[link]
                    
                    k = 1
                    count = target_queue_BMMs = 0
                    new_generation_time = ''

                    if link in self.BMM_Queue_Region_Count:
                        count = self.BMM_Queue_Region_Count[link]
                        target_queue_BMMs = int(queue_trigger.TargetBMMsPerSegment* current_region / queue_trigger.SegmentLength)
                        
                        if count < (0.95*target_queue_BMMs):
                            k = 0.9
                        elif count > (1.05*target_queue_BMMs):
                            k = 1.1

                    if k != 1:
                        queue_trigger.GenerationMeanTime[link] *= k
                        new_generation_time = queue_trigger.GenerationMeanTime[link]
                        self.BMM.recreateRandomGenerator(queue_trigger, link = link)
                        
                    if self.CF.Control['OutputLevel'] >= 2:
                        logger.info( queue_template.format(link, count, target_queue_BMMs, current_region, new_regions[link], queue_trigger.GenerationMeanTime[link]/k, new_generation_time) )
#-------------------------------------------------------------------------           
    def checkTurningSamplingRates(self):
        """Checks to see if message sampling rates are close to turning targets and changes generation times if not
        """
        turning_trigger = self.BMM.Triggers.triggers['Turning']
        
        if self.CF.Control['OutputLevel'] >= 2:
                    turning_template = '\t{0:15}|{1:8}|{2:15}|{3:15}|{4:15}|'
                    logger.info( '\nTurning\n' + turning_template.format('Intersection:','BMMs:','Target BMMs:', 'Current Lambda:', 'New Lambda:') )

        for intersection in turning_trigger.intersections:
            
            if intersection not in self.BMM_Intersection_Count:
                count = target_BMMs = 0
            else:
                count = self.BMM_Intersection_Count[intersection]
                target_BMMs = turning_trigger.TargetBMMsPerIntersection
            new_generation_time = ''
        
            k =1
            if count < (0.95*target_BMMs):
                k = 0.9
            elif count > (1.05*target_BMMs):
                k = 1.1

            if k != 1:
                turning_trigger.GenerationMeanTime[intersection] *= k
                new_generation_time = turning_trigger.GenerationMeanTime[intersection]
                self.BMM.recreateRandomGenerator(turning_trigger, link = intersection)
                        
            
            if self.CF.Control['OutputLevel'] >= 2:
               logger.info( turning_template.format(intersection, count, target_BMMs, turning_trigger.GenerationMeanTime[intersection]/k, new_generation_time) )

#-------------------------------------------------------------------------
    def checkTractionControl(self,tp):
        """Checks to see if message sampling rates are close to traction control targets and changes generation times if not
        """
        traction_trigger = self.BMM.Triggers.triggers['Traction Control']
        if traction_trigger.TargetSamplingRate != None:

            if self.CF.Control['OutputLevel'] >=2:
                traction_template = '\t{0:15}|{1:15}|{2:15}|{3:15}|'
                logger.info('\nTraction Control\n' + traction_template.format('BMMs:', 'Target BMMs:', 'Current Lambda:', 'New Lambda:') )

            if self.BMMCounts[traction_trigger.BMM_Type] > 0:
                count = self.BMMCounts['Traction Control']
                target = traction_trigger.TargetSamplingRate
            else:
                count = target = 0

            k = 1
            new_generation_time = ''

            if count < 0.95* target:
                k = 0.9
            elif count > 1.05* target:
                k = 1.1
                
            if k != 1:
                traction_trigger.GenerationMeanTime[-1] *= k
                self.BMM.recreateRandomGenerator(traction_trigger)

                new_generation_time = traction_trigger.GenerationMeanTime[-1]


            if self.CF.Control['OutputLevel'] >= 2:
                logger.info(traction_template.format(count,target, traction_trigger.GenerationMeanTime[-1]/k, new_generation_time))

        #Burst information    
        if len(self.BMM.burst_extensions) >0 and self.CF.Control['OutputLevel'] >=2:
            burst_template = '\t{0:35}|{1:15}|{2:15}|{3:5}'
            expired = []
            logger.info('\nBursts\n' + burst_template.format('Burst Trigger', 'Start Time', 'Expiration Time', 'Extensions'))
            for trigger, info in self.BMM.burst_extensions.iteritems():
                logger.info( burst_template.format(trigger.title, info[1], info[2], info[0] ) )

#-------------------------------------------------------------------------           
    def checkQueueRegion(self):
        """Determines the new regions for all the queue regions based on the transmitted MessageSize
        :return: a dictionary of all the new region lengths
        """
        new_regions = {}
        for link in self.BMM.Triggers.triggers['Queue'].queue_estimation.keys():    
            if link not in self.BMM_Queue_X.keys() or min(self.BMM_Queue_X[link]) >= 100:
                new_regions[link] = 100

            else:
                self.BMM_Queue_X[link] = sorted(self.BMM_Queue_X[link], reverse = True)
                new_regions[link] = self.QueueRegion(link, 0)
        return new_regions
#-------------------------------------------------------------------------

    def QueueRegion(self, link, farthest_x):
        """Extends the region until there are no more messages within 100 ft. 
        :return: The farthest away message + 100 ft. This is the new queue region
        """
        for bmm_x in self.BMM_Queue_X[link]:
            if farthest_x < bmm_x < farthest_x + 100:
                return self.QueueRegion(link, bmm_x)
        return farthest_x + 100
        