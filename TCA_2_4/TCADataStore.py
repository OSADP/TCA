#standard
import math


from warnings import simplefilter
simplefilter(action = "ignore", category = UserWarning)

#TCA
from TCACore import Timer, logger, Get_Heading, Get_Heading_Change


class DataStorage(object):

    def __init__(self, RandomGen, accel_included=False, link_included = False):
        """
        Initializes a DataStorage module

        :param RandomGen: The random seed
        :param accel_included: Whether acceleration data is included in the input
        """
        self.current_veh = {}

        self.all_veh = {}

        self.RG = RandomGen

        if accel_included:
            self.core_cols = [
                'time',
                'speed',
                'location_x',
                'location_y',
                'accel_instantaneous',]
        else:
            self.core_cols = [
                'time',
                'speed',
                'location_x',
                'location_y',]

        if link_included:
            self.core_cols.append('link')
            self.core_cols.append('link_x')

        self.veh_count = 0
        self.equipped_veh_count = 0

        self.PDM_count = 0
        self.PDM_DSRC_count = 0
        self.PDM_cell_count = 0
        self.PDM_both_count = 0

        self.BSM_count = 0
        self.BSM_DSRC_count = 0
        self.BSM_cell_count = 0
        self.BSM_both_count = 0

        self.BSM_PDM_count = 0
        self.BSM_PDM_DSRC_count = 0
        self.BSM_PDM_cell_count = 0
        self.BSM_PDM_both_count = 0

        self.CAM_count = 0
        self.CAM_DSRC_count = 0
        self.CAM_cell_count = 0
        self.CAM_both_count = 0

        self.SPOT_count = 0
        self.DIDC_count = 0

        self.timer = Timer(enabled=False)



    def find_veh_type(self, CF, RandomGen, veh):
        """
        Uses random seed to assign equippage type to given vehicle

        :param CF: Dictionary containing control file inputs
        :param RandomGen: The random seed
        :param veh: The vehicle to assign equipment to
        :return:
            PDM_equipped: True if vehicle can send PDMs, otherwise false
            BSM_equipped: True if vehicle can send BSMs, otherwise false
            CAM_equipped: True if vehicle can send CAMs, otherwise false
            SPOT_equipped: True if vehicle can send SPOT messages, otherwise false
            DSRC_enabled: True if vehicle can transmit messages via DSRC, otherwise false
            cellular_enabled: True if vehicle can transmit messages via cellular, otherwise false
        """

        PDM_equipped = False
        BSM_equipped = False
        CAM_equipped = False
        SPOT_equipped = False
        DIDC_equipped = False

        DSRC_enabled = False
        cellular_enabled = False
        self.veh_count +=1

        #if Type based information
        if (CF.Control['PDMVehicleTypes'] != []) or (CF.Control['BSMVehicleTypes'] != []) \
            or (CF.Control['DualPDMBSMVehicleTypes'] != []) or (CF.Control['CAMVehicleTypes'] != []) \
            or (CF.Control['SPOTVehicleTypes'] != []) or (CF.Control['DIDCVehicleTypes'] != []):

                if 'type' in veh.keys():
                    v_type = int(veh['type'])

                if v_type in CF.Control['PDMVehicleTypes']:
                    PDM_equipped = True

                if v_type in CF.Control['BSMVehicleTypes']:
                    BSM_equipped = True

                if v_type in CF.Control['CAMVehicleTypes']:
                    CAM_equipped = True

                if v_type in CF.Control['SPOTVehicleTypes']:
                    SPOT_equipped = True

                if v_type in CF.Control['DIDCVehicleTypes']:
                    DIDC_equipped = True
                    cellular_enabled = True

                if v_type in CF.Control['DualPDMBSMVehicleTypes']:
                    BSM_equipped = True
                    PDM_equipped = True

                if (v_type in CF.Control['PDMDSRCVehicleTypes']) or  \
                   (v_type in CF.Control['BSMDSRCVehicleTypes']) or \
                   (v_type in CF.Control['PDMBSMDSRCVehicleTypes']) or \
                   (v_type in CF.Control['CAMDSRCVehicleTypes']):
                    DSRC_enabled = True

                if (v_type in CF.Control['PDMCellularVehicleTypes']) or  \
                   (v_type in CF.Control['BSMCellularVehicleTypes']) or \
                   (v_type in CF.Control['PDMBSMCellularVehicleTypes']):
                    cellular_enabled = True

                if (v_type in CF.Control['PDMDualCommVehicleTypes']) or  \
                   (v_type in CF.Control['BSMDualCommVehicleTypes']) or \
                   (v_type in CF.Control['PDMBSMDualCommVehicleTypes']):
                    cellular_enabled = True
                    DSRC_enabled = True

        # if ID based
        elif (CF.Control['PDMVehicleIDs'] != []) or (CF.Control['BSMVehicleIDs'] != []) \
            or (CF.Control['DualPDMBSMVehicleIDs'] != []) or (CF.Control['CAMVehicleIDs'] != []) \
            or (CF.Control['SPOTVehicleIDs'] != []) or (CF.Control['DIDCVehicleIDs'] != []):
                
                v_id = veh['vehicle_ID']
                try:
                    v_id = int(v_id)
                except:
                    pass

                if v_id in CF.Control['PDMVehicleIDs']:
                    PDM_equipped = True


                if v_id in CF.Control['BSMVehicleIDs']:
                    BSM_equipped = True


                if v_id in CF.Control['CAMVehicleIDs']:
                    CAM_equipped = True

                if v_id in CF.Control['SPOTVehicleIDs']:
                    SPOT_equipped = True

                if v_id in CF.Control['DIDCVehicleIDs']:
                    DIDC_equipped = True
                    cellular_enabled = True

                if v_id in CF.Control['DualPDMBSMVehicleIDs']:
                    BSM_equipped = True
                    PDM_equipped = True

                if (v_id in CF.Control['PDMDSRCVehicleIDs']) or  \
                   (v_id in CF.Control['BSMDSRCVehicleIDs']) or \
                   (v_id in CF.Control['PDMBSMDSRCVehicleIDs']) or \
                   (v_id in CF.Control['CAMDSRCVehicleIDs']):
                    DSRC_enabled = True

                if (v_id in CF.Control['PDMCellularVehicleIDs']) or  \
                   (v_id in CF.Control['BSMCellularVehicleIDs']) or \
                   (v_id in CF.Control['PDMBSMCellularVehicleIDs']):
                    cellular_enabled = True

                if (v_id in CF.Control['PDMDualCommVehicleIDs']) or  \
                   (v_id in CF.Control['BSMDualCommVehicleIDs']) or \
                   (v_id in CF.Control['PDMBSMDualCommVehicleIDs']):
                    cellular_enabled = True
                    DSRC_enabled = True

        #if Market penetration based
        elif (CF.Control['PDMMarketPenetration'] + CF.Control['BSMMarketPenetration']
                  + CF.Control['DualPDMBSMMarketPenetration'] + CF.Control['CAMMarketPenetration']
                  + CF.Control['SPOTMarketPenetration']  + CF.Control['DIDCMarketPenetration'] > 0):

            percentage_type  = self.RG['TypePercent']
            percentage_comm  =  self.RG['TypePercent']

            #if equipped
            if percentage_type <= (CF.Control['PDMMarketPenetration'] + CF.Control['BSMMarketPenetration'] + \
                               CF.Control['DualPDMBSMMarketPenetration'] + CF.Control['CAMMarketPenetration']
                                + CF.Control['SPOTMarketPenetration']) + CF.Control['DIDCMarketPenetration']:
        
                #if PDM only
                if percentage_type <= CF.Control['PDMMarketPenetration']:
                        PDM_equipped = True

                        if percentage_comm <= CF.Control['PDMDSRCMarketPenetration']:
                                DSRC_enabled = True

                        if DSRC_enabled == False:
                            if (CF.Control['PDMDSRCMarketPenetration'] + 1) <=  percentage_comm  <= \
                               (CF.Control['PDMCellularMarketPenetration'] +  CF.Control['PDMDSRCMarketPenetration']):
                                    cellular_enabled = True

                        if DSRC_enabled == False and cellular_enabled == False:
                            if (CF.Control['PDMDSRCMarketPenetration'] + CF.Control['PDMCellularMarketPenetration'] + 1) \
                                <=  percentage_comm  <= \
                               (CF.Control['PDMDualCommMarketPenetration'] +  CF.Control['PDMDSRCMarketPenetration']
                                + CF.Control['PDMCellularMarketPenetration']):
                                    cellular_enabled = True
                                    DSRC_enabled = True

                #if BSM only
                if ((CF.Control['PDMMarketPenetration'] + 1) <=  percentage_type)  and \
                        (percentage_type <= (CF.Control['BSMMarketPenetration'] +  CF.Control['PDMMarketPenetration'])):
                        BSM_equipped = True

                        if percentage_comm <= CF.Control['BSMDSRCMarketPenetration']:
                                DSRC_enabled = True

                        if DSRC_enabled == False:
                            if (CF.Control['BSMDSRCMarketPenetration'] + 1) <=  percentage_comm  <= \
                               (CF.Control['BSMCellularMarketPenetration'] +  CF.Control['BSMDSRCMarketPenetration']):
                                    cellular_enabled = True

                        if DSRC_enabled == False and cellular_enabled == False:
                            if (CF.Control['BSMDSRCMarketPenetration'] + CF.Control['BSMCellularMarketPenetration'] + 1) \
                                <=  percentage_comm  <= \
                               (CF.Control['BSMDualCommMarketPenetration'] +  CF.Control['BSMDSRCMarketPenetration']
                                + CF.Control['BSMCellularMarketPenetration']):
                                    cellular_enabled = True
                                    DSRC_enabled = True

                #if dual
                if ((CF.Control['PDMMarketPenetration'] + CF.Control['BSMMarketPenetration'] + 1) <=  percentage_type) and \
                   (percentage_type  <= (CF.Control['PDMMarketPenetration'] + CF.Control['BSMMarketPenetration']
                    + CF.Control['DualPDMBSMMarketPenetration'])):
                        BSM_equipped = True
                        PDM_equipped = True

                        if percentage_comm <= CF.Control['PDMBSMDSRCMarketPenetration']:
                                DSRC_enabled = True

                        if DSRC_enabled == False:
                            if (CF.Control['PDMBSMDSRCMarketPenetration'] + 1) <=  percentage_comm  <= \
                               (CF.Control['PDMBSMCellularMarketPenetration'] +  CF.Control['PDMBSMDSRCMarketPenetration']):
                                    cellular_enabled = True


                        if DSRC_enabled == False and cellular_enabled == False:
                            if (CF.Control['PDMBSMDSRCMarketPenetration'] + CF.Control['PDMBSMCellularMarketPenetration'] + 1) \
                                <=  percentage_comm  <= \
                               (CF.Control['PDMBSMDualCommMarketPenetration'] +  CF.Control['PDMBSMDSRCMarketPenetration']
                                + CF.Control['PDMBSMCellularMarketPenetration']):
                                    cellular_enabled = True
                                    DSRC_enabled = True

                #if CAM only
                if ((CF.Control['PDMMarketPenetration'] +  CF.Control['BSMMarketPenetration'] + CF.Control['DualPDMBSMMarketPenetration'] + 1) <=  percentage_type)  and \
                    (percentage_type  <= (CF.Control['PDMMarketPenetration'] + CF.Control['BSMMarketPenetration'] + CF.Control['DualPDMBSMMarketPenetration'] + CF.Control['CAMMarketPenetration'])):
                        CAM_equipped = True
                        # CF.Control['CAMVehicleIDs'].append(veh['vehicle_ID'])

                        if percentage_comm <= CF.Control['CAMDSRCMarketPenetration']:
                                cellular_enabled = True  # TODO - make this DSRC/cellular - DSRC_enabled = True
                                # CF.Control['CAMDSRCVehicleIDs'].append(veh['vehicle_ID']
                #if SPOT only
                if ((CF.Control['PDMMarketPenetration'] +  CF.Control['BSMMarketPenetration'] + CF.Control['DualPDMBSMMarketPenetration'] + CF.Control['CAMMarketPenetration'] + 1) <= \
                    percentage_type)  and (percentage_type  <= (CF.Control['PDMMarketPenetration'] + CF.Control['BSMMarketPenetration'] + CF.Control['DualPDMBSMMarketPenetration']
                    + CF.Control['CAMMarketPenetration'] + CF.Control['SPOTMarketPenetration'])):
                        SPOT_equipped = True
                        DSRC_enabled = True

                #if DIDC only
                if ((CF.Control['PDMMarketPenetration'] +  CF.Control['BSMMarketPenetration'] + CF.Control['DualPDMBSMMarketPenetration'] + CF.Control['CAMMarketPenetration'] + CF.Control['SPOTMarketPenetration'] + 1) <= \
                    percentage_type)  and (percentage_type  <= (CF.Control['PDMMarketPenetration'] + CF.Control['BSMMarketPenetration'] + CF.Control['DualPDMBSMMarketPenetration']
                    + CF.Control['CAMMarketPenetration'] + CF.Control['SPOTMarketPenetration'] + CF.Control['DIDCMarketPenetration'])):
                        DIDC_equipped = True
                        DSRC_enabled = True
            

        if (PDM_equipped and BSM_equipped):
            self.BSM_PDM_count +=1
            if (cellular_enabled and DSRC_enabled):
                self.BSM_PDM_both_count +=1
            elif DSRC_enabled:
                self.BSM_PDM_DSRC_count +=1
            elif cellular_enabled:
                self.BSM_PDM_cell_count +=1
        elif PDM_equipped:
            self.PDM_count +=1
            if (cellular_enabled and DSRC_enabled):
                self.PDM_both_count +=1
            elif DSRC_enabled:
                self.PDM_DSRC_count +=1
            elif cellular_enabled:
                self.PDM_cell_count +=1
        elif BSM_equipped:
            self.BSM_count +=1
            if (cellular_enabled and DSRC_enabled):
                self.BSM_both_count +=1
            elif DSRC_enabled:
                self.BSM_DSRC_count +=1
            elif cellular_enabled:
                self.BSM_cell_count +=1
        elif CAM_equipped:
            self.CAM_count +=1
            if (cellular_enabled and DSRC_enabled):
                self.CAM_both_count +=1
            elif DSRC_enabled:
                self.CAM_DSRC_count +=1
            elif cellular_enabled:
                self.CAM_cell_count +=1
        elif SPOT_equipped:
            self.SPOT_count += 1
        elif DIDC_equipped:
            self.DIDC_count += 1
        if PDM_equipped or BSM_equipped or CAM_equipped or SPOT_equipped or DIDC_equipped:
            self.equipped_veh_count +=1


        return PDM_equipped, BSM_equipped, CAM_equipped, SPOT_equipped, DSRC_enabled, cellular_enabled, DIDC_equipped



    def list_veh_counts(self):
        """
        Outputs the number of vehicles with each type of equippage to the log file

        """
        logger.info('Total Number Vehicles %s (Equipped Vehicles %s)' % (str(self.veh_count), str(self.equipped_veh_count)) )
        logger.info('PDM only %s (DSRC %s, Celluar %s, Dual %s) '
              % (str(self.PDM_count), str(self.PDM_DSRC_count), str(self.PDM_cell_count),  str(self.PDM_both_count) ))
        logger.info('BSM only %s (DSRC %s, Celluar %s, Dual %s) '
              % (str(self.BSM_count), str(self.BSM_DSRC_count), str(self.BSM_cell_count), str(self.BSM_both_count) ))
        logger.info('PDM and BSM %s (DSRC %s, Celluar %s, Dual %s) '
              % (str(self.BSM_PDM_count), str(self.BSM_PDM_DSRC_count), str(self.BSM_PDM_cell_count), str(self.BSM_PDM_both_count) ))

        logger.info('CAM only %s (DSRC %s, Celluar %s, Dual %s) '
              % (str(self.CAM_count), str(self.CAM_DSRC_count), str(self.CAM_cell_count), str(self.CAM_both_count) ))
        logger.info('SPOT only %s (DSRC %s) '
              % (str(self.SPOT_count), str(self.SPOT_count) ))
        logger.info('DIDC %s (DualComm %s) '
              % (str(self.DIDC_count), str(self.DIDC_count) ))


    def remove_non_active_vehicles(self, vehicles):
        """
        Removes vehicles that are no longer in the network from the table
        :param vehicles: List of vehicles that are currently being stored in the table
        """
        vehicles_id = [x['vehicle_ID'] for x in vehicles]

        non_active_vehs =  list(set(self.current_veh.keys()) - set(vehicles_id))

        for non_active_veh in non_active_vehs:

            del self.current_veh[non_active_veh]



    def pull_veh_data(self, veh, CF, RandomGen, Regions, tp, msgs):
        """
        Returns the vehicle data for a given vehicle at a given time period.
        If vehicle is already in network, updates vehicle time in network,
        distance traveled, acceleration, heading and yaw rate.
        If vehicle is new to network, calls find_veh_type and initializes
        vehicle data record dictionary

        :param veh: The vehicle to get data for
        :param CF: The dictionary containing control file inputs
        :param RandomGen: The random seed
        :param Regions: Cellular regions definition
        :param tp: The time to get vehicle data in
        :return: The vehicle data record dictionary
        """

        veh_data = None

        #update active equipped vehicle
        if (veh['vehicle_ID'] in self.current_veh.keys()) and (self.current_veh[veh['vehicle_ID']] is not None):

            veh_data = self.current_veh[veh['vehicle_ID']]


            for col in self.core_cols:
                veh_data[col] = veh[col]

            veh_data['time_out_network'] = 0

            veh_data['new_distance'] = math.sqrt(
                           (veh_data['location_y'] - veh_data['location_y_last']) ** 2 +
                           (veh_data['location_x'] - veh_data['location_x_last']) ** 2)

            veh_data['total_dist_traveled'] += veh_data['new_distance']


            if 'accel_instantaneous' in veh.keys():
                veh_data['accel_instantaneous'] = veh['accel_instantaneous']
            else:
                # Calculate average acceleration (convert speed from mph to ft/s)
                veh_data['average_acceleration'] =  ((veh_data['speed'] - veh_data['speed_last']) * 5280 / 3600) \
                                                   / (veh_data['time'] - veh_data['time_last'])



            # Only change heading if the vehicle has moved since the last timestep (otherwise heading will be falsely zero)
            if round(veh_data['new_distance'],1) != 0:
                new_heading = Get_Heading(veh_data['location_x_last'], veh_data['location_y_last'],
                                          veh_data['location_x'], veh_data['location_y'])
            else:
                new_heading = veh_data['heading']

            if new_heading != None:
                veh_data['previous_headings'][veh_data['time']] = new_heading

            for time in veh_data['previous_headings'].keys():
                if time + 2.0 < veh_data['time']:
                    veh_data['previous_headings'].pop(time)


            if len(veh_data['previous_headings']) > 1:
                veh_data['yawrate'] = Get_Heading_Change(veh_data['previous_headings'][min(veh_data['previous_headings'].keys())], new_heading) / (veh_data['time'] - min(veh_data['previous_headings'].keys()))
            else:
                veh_data['yawrate'] = 0

            veh_data['heading'] = new_heading

            veh_data['time'] = tp

        else:

            if (veh['vehicle_ID'] not in self.current_veh.keys()):

                if veh['vehicle_ID'] not in self.all_veh.keys():
                #Determine vehicle type
                    PDM_equipped, BSM_equipped, CAM_equipped, SPOT_equipped, DSRC_enabled, cellular_enabled, DIDC_equipped = self.find_veh_type(CF, RandomGen, veh)
                    self.all_veh[veh['vehicle_ID']] = {}
                    self.all_veh[veh['vehicle_ID']]['PDM_equipped'] = PDM_equipped
                    self.all_veh[veh['vehicle_ID']]['BSM_equipped'] = BSM_equipped
                    self.all_veh[veh['vehicle_ID']]['CAM_equipped'] = CAM_equipped
                    self.all_veh[veh['vehicle_ID']]['SPOT_equipped'] = SPOT_equipped
                    self.all_veh[veh['vehicle_ID']]['DSRC_enabled'] = DSRC_enabled
                    self.all_veh[veh['vehicle_ID']]['cellular_enabled'] = cellular_enabled 
                    self.all_veh[veh['vehicle_ID']]['DIDC_equipped'] = DIDC_equipped

                else:
                    PDM_equipped = self.all_veh[veh['vehicle_ID']]['PDM_equipped']
                    BSM_equipped = self.all_veh[veh['vehicle_ID']]['BSM_equipped']
                    CAM_equipped = self.all_veh[veh['vehicle_ID']]['CAM_equipped']
                    SPOT_equipped = self.all_veh[veh['vehicle_ID']]['SPOT_equipped']
                    DSRC_enabled = self.all_veh[veh['vehicle_ID']]['DSRC_enabled']
                    cellular_enabled = self.all_veh[veh['vehicle_ID']]['cellular_enabled']
                    DIDC_equipped = self.all_veh[veh['vehicle_ID']]['DIDC_equipped']



                
                if PDM_equipped or BSM_equipped or CAM_equipped or SPOT_equipped or DIDC_equipped:

                    if 'type' in veh.keys():
                       v_type = int(veh['type'])
                    else:
                       v_type = None

                    if 'accel_instantaneous' in veh.keys():
                       accel_instantaneous = veh['accel_instantaneous']
                    else:
                       accel_instantaneous = None

                    if 'link_x' in veh.keys():
                        link_x =veh['link_x']
                    else:
                        link_x = 'NA'

                    if 'link' in veh.keys():
                        link = veh['link']
                    else:
                        link = 'NA'

                    if 'length' in veh.keys():
                        veh_length = veh['length']
                    else:
                        veh_length = None

                    if 'width' in veh.keys():
                        veh_width = veh['width']
                    else:
                        veh_width = None


                    # Add vehicle to list
                    self.current_veh[veh['vehicle_ID']] = {
                            'vehicle_ID' : veh['vehicle_ID'],
                            'vehicle_type' : v_type,
                            'time': tp,
                            'time_last' : 0.0,
                            'speed': veh['speed'],
                            'speed_last' : -30,
                            'location_x': veh['location_x'],
                            'location_y': veh['location_y'],
                            'location_x_last' : 0.0,
                            'location_y_last' : 0.0,
                            'DSRC_enabled' : DSRC_enabled,
                            'cellular_enabled' : cellular_enabled,
                            'PDM_equipped' : PDM_equipped,
                            'BSM_equipped' : BSM_equipped,
                            'CAM_equipped' : CAM_equipped,
                            'SPOT_equipped' : SPOT_equipped,
                            'DIDC_equipped' : DIDC_equipped,
                            'heading' : None,
                            'yawrate' : 0,
                            'previous_headings' : {},

                            'total_dist_traveled' : 0.0,

                            'average_acceleration' : None,
                            'accel_instantaneous' : accel_instantaneous,
                            'length' : veh_length,
                            'width' : veh_width,
                    }

                    if PDM_equipped:
                       self.current_veh[veh['vehicle_ID']]['total_time_in_network'] = 0.0
                       self.current_veh[veh['vehicle_ID']]['time_out_network'] = 0.0
                       self.current_veh[veh['vehicle_ID']]['vehicle_ID_buffer_empty'] = True
                       self.current_veh[veh['vehicle_ID']]['vehicle_SS_buffer_empty'] = True
                       self.current_veh[veh['vehicle_ID']]['SS_count_generated_by_vehicle'] = 0
                       self.current_veh[veh['vehicle_ID']][ 'SS_count_in_vehicle'] = 0
                       self.current_veh[veh['vehicle_ID']]['time_to_next_periodic'] = 0.0
                       self.current_veh[veh['vehicle_ID']]['distance_to_next_periodic'] = 0.0
                       self.current_veh[veh['vehicle_ID']]['time_motionless'] = 0.0
                       self.current_veh[veh['vehicle_ID']]['time_of_last_stop'] = -1000
                       self.current_veh[veh['vehicle_ID']]['distance_of_last_stop'] = 1000.0
                       self.current_veh[veh['vehicle_ID']]['time_stamp_of_ID'] = -1000
                       self.current_veh[veh['vehicle_ID']]['PSN'] = msgs['PDM'].random_generator['psn']
                       self.current_veh[veh['vehicle_ID']]['looking_for_start'] = False
                       self.current_veh[veh['vehicle_ID']]['in_privacy_gap'] = False
                       self.current_veh[veh['vehicle_ID']]['privacy_gap_start'] = 0
                       self.current_veh[veh['vehicle_ID']]['distance_in_privacy_gap'] = 0.0
                       self.current_veh[veh['vehicle_ID']]['PSN_time_to_end_gap'] = 0.0
                       self.current_veh[veh['vehicle_ID']]['PSN_start_time'] = 0.0
                       self.current_veh[veh['vehicle_ID']]['PSN_start_distance'] = 0.0
                       self.current_veh[veh['vehicle_ID']]['PSN_distance_to_change'] = float(CF.Strategy["DistanceBetweenPSNSwitches"])
                       self.current_veh[veh['vehicle_ID']]['PSN_change_ID'] = 0
                       self.current_veh[veh['vehicle_ID']]['PSN_distance_to_end_of_gap'] = 0.0
                       self.current_veh[veh['vehicle_ID']]['PSN_time_to_end_of_PSN'] = float(veh['time']) + float(CF.Strategy['TimeBetweenPSNSwitches'])
                       self.current_veh[veh['vehicle_ID']]['new_distance'] = 0.0
                       self.current_veh[veh['vehicle_ID']]['time_of_start_snapshot'] = 0
                       self.current_veh[veh['vehicle_ID']]['time_of_periodic_snapshot'] = 0
                       self.current_veh[veh['vehicle_ID']]['prev_time_PDM_dsrc_transmit'] = -1000
                       self.current_veh[veh['vehicle_ID']]['prev_time_PDM_cellular_transmit'] = -1000
                       self.current_veh[veh['vehicle_ID']]['dsrc_transmit_pdm'] = False
                       self.current_veh[veh['vehicle_ID']]['last_RSE_transmitted_to'] = -1


                    if BSM_equipped:
                        self.current_veh[veh['vehicle_ID']]['prev_time_BSM_dsrc_transmit'] = -1000
                        self.current_veh[veh['vehicle_ID']]['prev_time_BSM_cellular_transmit'] = -1000
                        self.current_veh[veh['vehicle_ID']]['BSM_tmp_ID'] = msgs['BSM'].random_generator['BSM_Tmp_ID']
                        self.current_veh[veh['vehicle_ID']]['BSM_time_to_ID_chg'] = float(veh['time']) + 300.0
                        self.current_veh[veh['vehicle_ID']]['dsrc_transmit_bsm'] = False
                        self.current_veh[veh['vehicle_ID']]['brake_status'] = '0000'
                        self.current_veh[veh['vehicle_ID']]['brake_pressure'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['hard_braking'] = 0
                        self.current_veh[veh['vehicle_ID']]['sent_percent888'] = 0

                    if CAM_equipped:
                        self.current_veh[veh['vehicle_ID']]['dsrc_transmit_cam'] = False
                        self.current_veh[veh['vehicle_ID']]['last_CAM_distance'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['last_CAM_speed'] = None
                        self.current_veh[veh['vehicle_ID']]['last_CAM_heading'] = None
                        self.current_veh[veh['vehicle_ID']]['last_CAM_time'] = 0
                        self.current_veh[veh['vehicle_ID']]['CAM_Station_ID'] = msgs['CAM'].random_generator['Station_ID']



                    if SPOT_equipped:
                        self.current_veh[veh['vehicle_ID']]['prev_SPOT_distance'] = None
                        self.current_veh[veh['vehicle_ID']]['prev_SPOT_speed'] = None
                        self.current_veh[veh['vehicle_ID']]['prev_SPOT_heading'] = None
                        self.current_veh[veh['vehicle_ID']]['prev_SPOT_accel'] = None
                        self.current_veh[veh['vehicle_ID']]['max_SPOT_accel'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['max_SPOT_yawrate'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['SPOT_accel_tp'] = None
                        self.current_veh[veh['vehicle_ID']]['SPOT_accel_X'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['SPOT_accel_Y'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['SPOT_accel_v'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['SPOT_accel_heading'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['SPOT_accel_yawrate'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['SPOT_yawrate_tp'] = None
                        self.current_veh[veh['vehicle_ID']]['SPOT_yawrate_X'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['SPOT_yawrate_Y'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['SPOT_yawrate_v'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['SPOT_yawrate_heading'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['SPOT_yawrate_accel'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['SPOT_trans_tp'] = None
                        self.current_veh[veh['vehicle_ID']]['prev_tp_travel_SPOT'] = None
                        self.current_veh[veh['vehicle_ID']]['prev_tp_accel_SPOT'] = None
                        self.current_veh[veh['vehicle_ID']]['prev_tp_yawrate_SPOT'] = None

                    if DIDC_equipped:
                        self.current_veh[veh['vehicle_ID']]['brake_status'] = '0000'                        
                        self.current_veh[veh['vehicle_ID']]['brake_pressure'] = 0.0
                        self.current_veh[veh['vehicle_ID']]['DSRC_enabled'] = True
                        self.current_veh[veh['vehicle_ID']]['cellular_enabled'] = True
                        self.current_veh[veh['vehicle_ID']]['active_triggers'] = {}
                        self.current_veh[veh['vehicle_ID']]['after_triggers']= {}

                        

                    if link is not None:
                        self.current_veh[veh['vehicle_ID']]['link'] = link
                    if link_x is not None:
                        self.current_veh[veh['vehicle_ID']]['link_x'] = link_x

                    if PDM_equipped or BSM_equipped or CAM_equipped or SPOT_equipped or DIDC_equipped:
                        if Regions is not None:
                            for Event in Regions.Event_titles:
                                self.current_veh[veh['vehicle_ID']][Event] = -9999
                            for Event_region in Regions.Event_regions:
                                e_region_title = Event_region.title 
                                for event_title in Event_region.events.keys():
                                    element_title = str(e_region_title) + '_' + str(event_title)
                                    self.current_veh[veh['vehicle_ID']][element_title] = -9999



                        self.current_veh[veh['vehicle_ID']]['TractionControl'] = -9999
                        self.current_veh[veh['vehicle_ID']]['GlobalLastCheck'] = tp
                        self.current_veh[veh['vehicle_ID']]['GlobalNextCheck'] = tp
                        veh_data = self.current_veh[veh['vehicle_ID']]


                else:
                    self.current_veh[veh['vehicle_ID']] = None


        return veh_data


    def previous_values(self, veh):
        """
        Sets previous value holders in vehicle data record equal to most recent
        values.
        :param veh: The vehicle to update previous values for
        """

        vehicle = self.current_veh[veh['vehicle_ID']]

        vehicle['speed_last'] = vehicle['speed']
        vehicle['time_last'] = vehicle['time']
        vehicle['location_x_last'] = vehicle['location_x']
        vehicle['location_y_last'] = vehicle['location_y']

