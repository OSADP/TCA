
#external
import pandas as pd

#tca
from TCACore import logger


class Trajectories(object):
    """Core class for reading vehicles trajectories"""

    def __init__(self, filename, output, file_type, rows_to_run = None):
        """

        :param filename: file name of trajectory file
        :param output: output level for logging
        :param file_type: type of file (csv, VISSIM)
        :param rows_to_run: How many rows to read in for debugging.  None is all.
        """
        self.rows_to_run = rows_to_run

        self.filename = filename
        self.filetype = file_type
        self.delimiter = ','
        self.unit_converter = 1.0

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

        self.equipped_veh_count = 0
        self.veh_count = 0


        self.link_included = False
        self.link_x_included = False

        if self.filetype == 'VISSIM' or self.filetype == 'VISSIM7':
            self.delimiter = ';'

        if self.filetype == 'VISSIM':
            self.unit_converter = 100 / 2.54 / 12

        if output > 0:
            logger.info('Loading Trajectory File: %s' % (self.filename))

    def read_header(self, line, CF):
           """
           Reads header of vehicle trajectory input file.
           Initializes self.cols.

           :param line: Line containing header information
           :param CF: Dictionary of control file inputs
           """
           #if a VISSIM file
           if self.filetype == 'VISSIM7':
                line = line.split(':')[1]
                header = [x.strip() for x in line.split(self.delimiter)]
                veh_id = 'NO'
                time = 'SIMSEC'
                speed = 'SPEED'
                coord = 'COORDFRONT'
                acc = 'ACCELERATION'
                link = 'LANE\LINK\NO'
                link_x = 'POS'
                type = 'VEHTYPE'
                
           elif self.filetype == 'VISSIM':
                header = [x.strip() for x in line.split(self.delimiter)][:-1]
                veh_id = 'VehNr'
                time = 't'
                speed = 'v'
                x = 'WorldX'
                y = 'WorldY'
                acc = 'a'
                type = 'Type'
                link = 'Link'
           elif self.filetype == 'CSV':
                header = [x.strip() for x in line.split(self.delimiter)]
                veh_id = CF.Control['IDColumn']
                time = CF.Control['TimeColumn']
                speed = CF.Control['SpdColumn']
                x = CF.Control['XColumn']
                y = CF.Control['YColumn']
                acc = CF.Control['AccelColumn']
                type = CF.Control['TypeColumn']


           self.cols = {}

           self.cols['veh_col'] = header.index(veh_id)
           self.cols['time_col']  = header.index(time)
           self.cols['speed_col']  = header.index(speed)
           try:
                self.cols['x_col']  = header.index(x)
                self.cols['y_col']  = header.index(y)
           except:
            self.cols['x_col'] = None
            self.cols['y_col'] = None

           try:
               self.cols['coord_col'] = header.index(coord)
           except:
               self.cols['coord_col'] = None 

           try:
               self.cols['link_col'] = header.index(link)
               self.link_included = True
           except:
               self.cols['link_col'] = None

           try:
               self.cols['acc_col'] = header.index(acc)
           except:
               self.cols['acc_col'] = None

           try:
               self.cols['type_col'] = header.index(type)
           except:
               self.cols['type_col'] = None
           try:
                self.cols['link_x_col'] = header.index(link_x)
                self.link_x_included = True
           except:
                self.cols['link_x_col'] = None

    def get_id(self, line):
        """
        Returns vehicle id from input line

        :param line: Line from vehicle trajectory input
        :return: The vehicle id in the input line
        """
        if self.filetype == 'VISSIM':
            data = line.split(self.delimiter)[:-1]
        else:
            data = line.split(self.delimiter)

        return data[self.cols['veh_col']].strip()


    def read_line(self, line):
        """
        Reads line from vehicle trajectory input and updates relevant local data records
        :param line: The line from vehicle trajectory input
        :return: None :raise: Exception if line does not contain correctly formed data
        """

        if self.filetype == 'VISSIM':
            data = line.split(self.delimiter)[:-1]
            # data = line.split(self.delimiter)

        else:
            data = line.split(self.delimiter)
        if len(data)>4:

            try:
                veh_dict = {
                          'vehicle_ID': data[self.cols['veh_col']].strip(),
                          'time': float(data[self.cols['time_col']].strip()),
                          'speed': float(data[self.cols['speed_col']].strip()),
                          }

                if self.filetype != 'VISSIM7': 
                    veh_dict['location_x'] = float(data[self.cols['x_col'] ].strip()) * self.unit_converter
                    veh_dict['location_y'] = float(data[self.cols['y_col']].strip()) * self.unit_converter
                
                else:
                    xy = data[self.cols['coord_col']].strip().split(' ')
                    veh_dict['location_x'] = float(xy[0]) * self.unit_converter
                    veh_dict['location_y'] = float(xy[1]) * self.unit_converter
                  
                if self.cols['acc_col'] is not None:
                    veh_dict['accel_instantaneous'] = float(data[self.cols['acc_col']].strip())
                if self.cols['type_col'] is not None:
                    veh_dict['type'] = float(data[self.cols['type_col']].strip())

                if self.cols['link_col'] is not None:
                    veh_dict['link'] = int(data[self.cols['link_col']].strip())
                if self.cols['link_x_col'] is not None:
                    veh_dict['link_x'] = float(data[self.cols['link_x_col']].strip())
                
                return veh_dict

            except:
                print data
                raise


        else:
            return None

    def find_veh_type(self, CF, RandomGen, veh):
        """
        For TCA multi core version.  Uses random seed to assign equippage type to given vehicle

        :param CF: Dictionary containing control file inputs
        :param RandomGen: The random seed
        :param veh: The vehicle to assign equipment to
        :return:
            PDM_equipped: True if vehicle can send PDMs, otherwise false
            BSM_equipped: True if vehicle can send BSMs, otherwise false
            DSRC_enabled: True if vehicle can transmit messages via DSRC, otherwise false
            cellular_enabled: True if vehicle can transmit messages via cellular, otherwise false
        """

        PDM_equipped = False
        BSM_equipped = False

        DSRC_enabled = False
        cellular_enabled = False
        # self.veh_count +=1


        #if Type based information
        if (CF.Control['PDMVehicleTypes'] != []) and (CF.Control['BSMVehicleTypes'] != []) \
            and (CF.Control['DualPDMBSMVehicleTypes'] != []):

                if 'type' in veh.keys():
                    v_type = int(veh['type'])

                if v_type in CF.Control['PDMVehicleTypes']:
                    PDM_equipped = True

                if v_type in CF.Control['BSMVehicleTypes']:
                    BSM_equipped = True

                if v_type in CF.Control['DualPDMBSMVehicleTypes']:
                    BSM_equipped = True
                    PDM_equipped = True

                if (v_type in CF.Control['PDMDSRCVehicleTypes']) or  \
                   (v_type in CF.Control['BSMDSRCVehicleTypes']) or \
                   (v_type in CF.Control['PDMBSMDSRCVehicleTypes']):
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
            and (CF.Control['DualPDMBSMVehicleIDs'] != []):

                v_id = veh['vehicle_ID']

                if v_id in CF.Control['PDMVehicleIDs']:
                    PDM_equipped = True

                if v_id in CF.Control['BSMVehicleIDs']:
                    BSM_equipped = True

                if v_id in CF.Control['DualPDMBSMVehicleIDs']:
                    BSM_equipped = True
                    PDM_equipped = True

                if (v_id in CF.Control['PDMDSRCVehicleIDs']) or  \
                   (v_id in CF.Control['BSMDSRCVehicleIDs']) or \
                   (v_id in CF.Control['PDMBSMDSRCVehicleIDs']):
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
                  + CF.Control['DualPDMBSMMarketPenetration']) > 0:

            percentage_type  = RandomGen['TypePercent']
            percentage_comm  =  RandomGen['TypePercent']

            #if equipped
            if percentage_type <= (CF.Control['PDMMarketPenetration'] + CF.Control['BSMMarketPenetration'] + \
                               CF.Control['DualPDMBSMMarketPenetration']):

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

        if PDM_equipped or BSM_equipped:
            self.equipped_veh_count +=1
        
        return PDM_equipped, BSM_equipped, DSRC_enabled, cellular_enabled

    def find_completed_vehicles(self, veh_in_tp, veh_data):
        """
        Checks to see which vehicles don't show up in the next time period and therefore have completed their trip.

        :param veh_in_tp: List of vehicles that were seen in the given time period
        :param veh_data: List of vehicles that are in the vehicle data records
        :return: List of vehicles that are no longer in the network
        """

        completed_vehicles =  list(set(veh_data.keys()) - set(veh_in_tp))

        return completed_vehicles


    def read_by_tp(self, CF):
        """
        Reads the vehicle trajectory input file line by line to provide trajectories by time period

        :param CF: Dictionary of control file inputs
        """

        c=0

        with open(self.filename) as in_f:

            if self.filetype == 'VISSIM':
                #find start of VISSIM data
                line = in_f.readline()
                while 'VehNr;' not in line:
                    line = in_f.readline()
            elif self.filetype == 'VISSIM7':
                line = in_f.readline()
                while '$VEHICLE' not in line:
                    line = in_f.readline()
            elif self.filetype == 'CSV':
                line = in_f.readline()

            self.read_header(line, CF)

            line = self.read_line(in_f.readline())

            old_tp = None
            tp_list = []

            while line:

                tp = line['time']

                if tp != old_tp:

                    if old_tp != None:
                        yield old_tp, tp_list

                    old_tp = tp
                    tp_list = []

                tp_list.append(line)
                line = self.read_line(in_f.readline())
                c +=1

            #yield last tp
            yield tp, tp_list

    def read_by_veh(self, CF, rows_to_run):

        """
        Reads the vehicle trajectory input file into a pandas dataframe all at once to provide full vehicle trajectories

        :param CF: Dictionary of control file inputs
        :param rows_to_run: Number of rows of the input file to read in
        :return: Pandas dataframe containing trajectory file input
        """

        df = pd.read_csv(filepath_or_buffer = CF.Control['TrajectoryFileName'],
                          sep = ';',
                          header = file_fzp_start(CF.Control['TrajectoryFileName']),
                          skipinitialspace = True,
                          usecols = ['VehNr', 't', 'a', 'v', 'WorldX', 'WorldY' ],
                          nrows = rows_to_run)

        df['WorldX'] = df['WorldX'].apply(lambda x: x * self.unit_converter)
        df['WorldY'] = df['WorldY'].apply(lambda x: x * self.unit_converter)

        df = df.rename(columns={
         'VehNr': 'vehicle_ID',
         't': 'time',
         'a': 'accel_instantaneous',
         'v': 'speed',
         'WorldX': 'location_x',
         'WorldY': 'location_y',
         })

        return df




