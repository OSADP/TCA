#standard
import math


from warnings import simplefilter
simplefilter(action = "ignore", category = UserWarning)

#TCA
from TCACore import logger, Get_Heading, Get_Heading_Change


class DataStorage(object):

    def __init__(self, RandomGen, accel_included=False):
        """
        Initializes a DataStorage module

        :param RandomGen: The random seed
        :param accel_included: Whether acceleration data is included in the input
        """
        self.db = {}

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

        DSRC_enabled = False
        cellular_enabled = False
        self.veh_count +=1


        #if Type based information
        if (CF.Control['PDMVehicleTypes'] != []) or (CF.Control['BSMVehicleTypes'] != []) \
            or (CF.Control['DualPDMBSMVehicleTypes'] != []) or (CF.Control['CAMVehicleTypes'] != []) \
            or (CF.Control['SPOTVehicleTypes'] != []):

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

        #if ID based
        elif (CF.Control['PDMVehicleIDs'] != []) or (CF.Control['BSMVehicleIDs'] != []) \
            or (CF.Control['DualPDMBSMVehicleIDs'] != []) or (CF.Control['CAMVehicleIDs'] != []) \
            or (CF.Control['SPOTVehicleIDs'] != []):

                v_id = int(veh['vehicle_ID'])

                if v_id in CF.Control['PDMVehicleIDs']:
                    PDM_equipped = True

                if v_id in CF.Control['BSMVehicleIDs']:
                    BSM_equipped = True

                if v_id in CF.Control['CAMVehicleIDs']:
                    CAM_equipped = True

                if v_id in CF.Control['SPOTVehicleIDs']:
                    SPOT_equipped = True

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

        #if Market pentration based
        elif (CF.Control['PDMMarketPenetration'] + CF.Control['BSMMarketPenetration']
                  + CF.Control['DualPDMBSMMarketPenetration'] + CF.Control['CAMMarketPenetration']
                  + CF.Control['SPOTMarketPenetration'] > 0):

            percentage_type  = self.RG['TypePercent']
            percentage_comm  =  self.RG['TypePercent']

            #if equipped
            if percentage_type <= (CF.Control['PDMMarketPenetration'] + CF.Control['BSMMarketPenetration'] + \
                               CF.Control['DualPDMBSMMarketPenetration'] + CF.Control['CAMMarketPenetration']
                                + CF.Control['SPOTMarketPenetration']):

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

                        if percentage_comm <= CF.Control['CAMDSRCMarketPenetration']:
                                DSRC_enabled = True


                #if SPOT only
                if ((CF.Control['PDMMarketPenetration'] +  CF.Control['BSMMarketPenetration'] + CF.Control['DualPDMBSMMarketPenetration'] + CF.Control['CAMMarketPenetration'] + 1) <=
                    percentage_type)  and (percentage_type  <= (CF.Control['PDMMarketPenetration'] + CF.Control['BSMMarketPenetration'] + CF.Control['DualPDMBSMMarketPenetration']
                    + CF.Control['CAMMarketPenetration'] + CF.Control['SPOTMarketPenetration'])):
                        SPOT_equipped = True
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
        if PDM_equipped or BSM_equipped or CAM_equipped or SPOT_equipped:
            self.equipped_veh_count +=1

        return PDM_equipped, BSM_equipped, CAM_equipped, SPOT_equipped, DSRC_enabled, cellular_enabled



    def list_veh_counts(self):
        """
        Outputs the number of vehicles with each type of equippage to the log file

        """
        logger.info('Total Number Vehicles %s (Equipped Vehicles %s)' % (str(self.veh_count), str(self.equipped_veh_count)) )
        logger.info('PDM only %s (DCRC %s, Celluar %s, Dual %s) '
              % (str(self.PDM_count), str(self.PDM_DSRC_count), str(self.PDM_cell_count),  str(self.PDM_both_count) ))
        logger.info('BSM only %s (DCRC %s, Celluar %s, Dual %s) '
              % (str(self.BSM_count), str(self.BSM_DSRC_count), str(self.BSM_cell_count), str(self.BSM_both_count) ))
        logger.info('PDM and BSM %s (DCRC %s, Celluar %s, Dual %s) '
              % (str(self.BSM_PDM_count), str(self.BSM_PDM_DSRC_count), str(self.BSM_PDM_cell_count), str(self.BSM_PDM_both_count) ))

        logger.info('CAM only %s (DCRC %s, Celluar %s, Dual %s) '
              % (str(self.CAM_count), str(self.CAM_DSRC_count), str(self.CAM_cell_count), str(self.CAM_both_count) ))
        logger.info('SPOT only %s (DCRC %s) '
              % (str(self.SPOT_count), str(self.SPOT_count) ))


    def remove_non_active_vehicles(self, vehicles):
        """
        Removes vehicles that are no longer in the network from the table
        :param vehicles: List of vehicles that are currently being stored in the table
        """

        vehicles_id = [x['vehicle_ID'] for x in vehicles]

        non_active_vehs =  list(set(self.db.keys()) - set(vehicles_id))

        for non_active_veh in non_active_vehs:
            del self.db[non_active_veh]




    def pull_veh_data(self, veh, CF, RandomGen, Regions, tp):
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

        #update active vehicle
        if veh['vehicle_ID'] in self.db.keys():




            veh_data = self.db[veh['vehicle_ID']]

            for col in self.core_cols:
                veh_data[col] = veh[col]

            veh_data['time_out_network'] = 0
            veh_data['total_time_in_network'] += (veh['time'] - veh_data['time_last'])

            veh_data['new_distance'] = math.sqrt(
                           (veh_data['location_y'] - veh_data['location_y_last']) ** 2 +
                           (veh_data['location_x'] - veh_data['location_x_last']) ** 2)

            veh_data['total_dist_traveled'] += veh_data['new_distance']

            veh_data['dsrc_transmit_pdm'] = False
            veh_data['dsrc_transmit_bsm'] = False
            veh_data['dsrc_transmit_cam'] = False

            if (veh_data['time'] - veh_data['time_last']) > 0.0:
                # Calculate average acceleration (convert speed from mph to ft/s)
                veh_data['average_acceleration'] =  ((veh_data['speed'] - veh_data['speed_last']) * 5280 / 3600) \
                                                   / (veh_data['time'] - veh_data['time_last'])


            if 'accel_instantaneous' in veh.keys():
                veh_data['accel_instantaneous'] = veh['accel_instantaneous']


            # Only change heading if the vehicle has moved since the last timestep (otherwise heading will be falsely zero)
            if float(veh_data['new_distance']) != 0:
                new_heading = Get_Heading(veh_data['location_x_last'], veh_data['location_y_last'],veh_data['location_x'], veh_data['location_y'])


                # Only set yaw rate if a previous heading exists
                if veh_data['heading'] != None:
                    veh_data['yawrate'] = Get_Heading_Change(veh_data['heading'],new_heading) / (veh_data['time'] - veh_data['time_last'])

                veh_data['heading'] = new_heading

            veh_data['time'] = tp

        #if new vehicle
        else:

            #Determine vehicle type
            PDM_equipped, BSM_equipped, CAM_equipped, SPOT_equipped, DSRC_enabled, cellular_enabled = self.find_veh_type(CF, RandomGen, veh)

            if 'type' in veh.keys():
               v_type = int(veh['type'])
            else:
               v_type = None

            if 'accel_instantaneous' in veh.keys():
               accel_instantaneous = veh['accel_instantaneous']
            else:
               accel_instantaneous = None

            # Add vehicle to list
            self.db[veh['vehicle_ID']] = {
                    'vehicle_ID' : veh['vehicle_ID'],
                    'vehicle_type' : v_type,
                    'total_time_in_network' : 0.0,
                    'time_out_network' : 0.0,
                    'total_dist_traveled' : 0.0,
                    'vehicle_ID_buffer_empty' : True,
                    'vehicle_SS_buffer_empty' : True,
                    'SS_count_generated_by_vehicle' : 0,
                    'SS_count_in_vehicle' : 0,
                    'time_to_next_periodic' : 0.0,
                    'distance_to_next_periodic' : 0.0,
                    'time_motionless' : 0.0,
                    'time_of_last_stop' : -1000,
                    'distance_of_last_stop' : 1000.0,
                    'time_stamp_of_ID' : -1000,
                    'PSN' : RandomGen['psn'],
                    'looking_for_start' : False,
                    'in_privacy_gap' : False,
                    'privacy_gap_start' : 0,
                    'PSN_time_to_end_gap' : 0.0,
                    'distance_in_privacy_gap' : 0.0,
                    'PSN_start_time' : 0.0,
                    'PSN_start_distance' : 0.0,
                    'PSN_distance_to_change' : float(CF.Strategy["DistanceBetweenPSNSwitches"]),
                    'PSN_change_ID' : 0,
                    'PSN_distance_to_end_of_gap' : 0.0,
                    'PSN_time_to_end_of_PSN' : float(veh['time']) + float(CF.Strategy['TimeBetweenPSNSwitches']),
                    'new_distance' : 0.0,
                    'location_x_last' : 0.0,
                    'location_y_last' : 0.0,
                    'time_last' : 0.0,
                    'speed_last' : -30,
                    'time': tp,
                    'speed': veh['speed'],
                    'location_x': veh['location_x'],
                    'location_y': veh['location_y'],
                    'time_of_start_snapshot' : 0,
                    'time_of_periodic_snapshot' : 0,
                    'prev_time_PDM_dsrc_transmit' : -1000,
                    'prev_time_BSM_dsrc_transmit' : -1000,
                    'prev_time_PDM_cellular_transmit' : -1000,
                    'prev_time_BSM_cellular_transmit' : -1000,
                    'DSRC_enabled' : DSRC_enabled,
                    'cellular_enabled' : cellular_enabled,
                    'average_acceleration' : None,
                    'accel_instantaneous' : accel_instantaneous,
                    'last_RSE_transmitted_to' : -1,
                    'PDM_equipped' : PDM_equipped,
                    'BSM_equipped' : BSM_equipped,
                    'CAM_equipped' : CAM_equipped,
                    'SPOT_equipped' : SPOT_equipped,
                    'dsrc_transmit_pdm' : False,
                    'dsrc_transmit_bsm' : False,
                    'dsrc_transmit_cam' : False,
                    'brake_status' : '0000',
                    'brake_pressure' : 0.0,
                    'hard_braking' : 0,
                    'sent_percent' : 0,
                    'heading' : None,
                    'yawrate' : None,
                    'last_CAM_distance' : 0.0,
                    'last_CAM_speed' : None,
                    'last_CAM_heading' : None,
                    'last_CAM_time' : None,
                    'prev_SPOT_distance' : None,
                    'prev_SPOT_speed' : None,
                    'prev_SPOT_heading' : None,
                    'prev_SPOT_accel' : None,
                    'max_SPOT_accel' : 0.0,
                    'max_SPOT_yawrate' : 0.0,
                    'SPOT_accel_tp' : None,
                    'SPOT_accel_X' : 0.0,
                    'SPOT_accel_Y' : 0.0,
                    'SPOT_accel_v' : 0.0,
                    'SPOT_accel_heading' : 0.0,
                    'SPOT_accel_yawrate' : 0.0,
                    'SPOT_yawrate_tp' : None,
                    'SPOT_yawrate_X' : 0.0,
                    'SPOT_yawrate_Y' : 0.0,
                    'SPOT_yawrate_v' : 0.0,
                    'SPOT_yawrate_heading' : 0.0,
                    'SPOT_yawrate_accel' : 0.0,
                    'SPOT_trans_tp' : None,
                    'prev_tp_travel_SPOT' : None,
                    'prev_tp_accel_SPOT' : None,
                    'prev_tp_yawrate_SPOT' : None,
                }
            if PDM_equipped or BSM_equipped or CAM_equipped or SPOT_equipped:
                if Regions is not None:
                    for Event in Regions.Event_titles:
                        self.db[veh['vehicle_ID']][Event] = -9999

                veh_data = self.db[veh['vehicle_ID']]


        return veh_data


    def previous_values(self, veh):
        """
        Sets previous value holders in vehicle data record equal to most recent
        values.
        :param veh: The vehicle to update previous values for
        """

        vehicle = self.db[veh['vehicle_ID']]

        vehicle['speed_last'] = vehicle['speed']
        vehicle['time_last'] = vehicle['time']
        vehicle['location_x_last'] = vehicle['location_x']
        vehicle['location_y_last'] = vehicle['location_y']
