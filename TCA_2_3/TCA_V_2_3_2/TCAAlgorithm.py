#Standard
import unittest

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


        self.msgs = {'BSM': self.BSM, 'CAM': self.CAM, 'SPOT': self.SPOT, 'PDM': self.PDM}

        self.tbl = DataStorage(self.random_generator, accel_included = True, link_included = link_included)

        #Each Vehicle RSE list
        self.VehicleRSE = {}

        #Limit of message list before printing to a file
        self.msg_limit = msg_limit


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
        # return self.tbl.pull_veh_data(veh = veh, CF = self.CF, RandomGen = self.random_generator, Regions = self.regions, tp = tp)

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
            or (veh_data['BSM_equipped']) or (veh_data['CAM_equipped']):


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


        