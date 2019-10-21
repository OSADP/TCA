#standard
import os
import random as rnd
import sys
import tempfile as tmpfile
import unittest
import logging

#external
import pandas as pd

#tca
from TCACore import logger

class Trajectories(object):
    """Core class for reading vehicles trajectories"""

    def __init__(self, CHUNK_SIZE = 20000000 ):

        self.CHUNK_SIZE = CHUNK_SIZE
        self.temp_files = []
        self.rnd = rnd.Random()
        self.rnd.seed(3)

        self.equip_PDM = []
        self.equip_BSM = []
        self.equip_DualPDMBSM = []

        self.PDM_DSRC = []
        self.PDM_Cellular = []
        self.PDM_DualComm = []

        self.BSM_DSRC = []
        self.BSM_Cellular = []
        self.BSM_DualComm = []

        self.PDMBSM_DSRC = []
        self.PDMBSM_Cellular = []
        self.PDMBSM_DualComm = []

        self.DSRC_list = []
        self.cellular_list = []
        self.dualcomm_list = []


    def __del__(self):
        for tmp in self.temp_files:
            os.remove(tmp)

    def open_trajectory_file(self, vissim_file, filename, skip_lines = 1, ):

        if not vissim_file:
             try:
                return pd.read_csv(filename,
                              iterator=True,
                              chunksize=self.CHUNK_SIZE,
                              skipinitialspace=True,
                              index_col=False,
                              )
             except:
                logger.error('Error: reading csv file.  Please check the format of the file')
                raise

        else:
            try:
                return pd.read_csv(filename,
                              iterator=True,
                              chunksize=self.CHUNK_SIZE,
                              sep=';',
                              skipinitialspace=True,
                              header=1,
                              index_col=False,
                              skiprows = skip_lines -1 )
            except:
                logger.error('Error: VISSIM fzp file does not have all required fields of: VehNr, t, WorldX, WorldY, and v')
                raise


#---------------------------------------------------------------
    def load(self, CF):

        self.vissim_file = False
        self.include_accel = False

        if CF.Control['FileType'].lower()  == 'vissim' or CF.Control['FileType'].lower()  == 'fzp':
            self.vissim_file = True

        if self.vissim_file:
            line_skip = 0
            CF.Control['AccelColumn'] = True
            with open(CF.Control['TrajectoryFileName']) as in_f:
                line = in_f.readline()
                while 'VehNr;' not in line:
                    line = in_f.readline()
                    line_skip += 1

        if CF.Control['OutputLevel'] >=1:
            logger.info('Loading %s' % (CF.Control['TrajectoryFileName'].split('/')[-1]))

        #Determine Market Penetration
        if (CF.Control['PDMMarketPenetration'] != None) or (CF.Control['BSMMarketPenetration'] != None) or \
           (CF.Control['DualPDMBSMMarketPenetration'] != None):

            if not self.vissim_file:
                _infile = self.open_trajectory_file( self.vissim_file, CF.Control['TrajectoryFileName'])
            else:
                _infile = self.open_trajectory_file( self.vissim_file, CF.Control['TrajectoryFileName'],
                                                     skip_lines = line_skip )
            IDs = []

            #Determine Equipped Vehicles based on MarkPenetration
            file_num = 0
            for chunk in _infile:
               file_num += 1
               if self.vissim_file:
                   IDs = list(set(IDs + list(chunk['VehNr'].unique())))
               else:
                   IDs = list(set(IDs + list(chunk[CF.Control['IDColumn']].unique())))

            # print 'Temp Files # ', str(file_num)

            if CF.Control['OutputLevel'] >=1:
                logger.info('Read in %s vehicle IDs' % (str(len(IDs))))

            if CF.Control['DualPDMBSMMarketPenetration'] != None:
                num_Dual_PDMBSM =  int(round(len(IDs) * (CF.Control['DualPDMBSMMarketPenetration'] / 100.0)))
                self.equip_DualPDMBSM = self.rnd.sample(IDs, num_Dual_PDMBSM)

                Sub_id_list = [ID for ID in self.equip_DualPDMBSM]
                if CF.Control['PDMBSMDSRCMarketPenetration'] != None:
                    num_PDMBSM_DSRC = int(round(len(self.equip_DualPDMBSM) * (CF.Control['PDMBSMDSRCMarketPenetration'] / 100.00)))
                    self.PDMBSM_DSRC = self.rnd.sample(Sub_id_list, num_PDMBSM_DSRC)
                    Sub_id_list = [ID for ID in self.equip_DualPDMBSM if ID not in self.PDMBSM_DSRC]

                if CF.Control['PDMBSMCellularMarketPenetration'] != None:
                    num_PDMBSM_Cellular = int(round(len(self.equip_DualPDMBSM) * (CF.Control['PDMBSMCellularMarketPenetration'] / 100.00)))
                    if len(Sub_id_list) < num_PDMBSM_Cellular:
                        num_PDMBSM_Cellular = len(Sub_id_list)
                    self.PDMBSM_Cellular = self.rnd.sample(Sub_id_list, num_PDMBSM_Cellular)
                    Sub_id_list = [ID for ID in self.equip_DualPDMBSM if ID not in self.PDMBSM_Cellular and ID not in self.PDMBSM_DSRC]

                if CF.Control['PDMBSMDualCommMarketPenetration'] != None:
                    num_PDMBSM_DualComm = int(round(len(self.equip_DualPDMBSM) * (CF.Control['PDMBSMDualCommMarketPenetration'] / 100.00)))
                    if len(Sub_id_list) < num_PDMBSM_DualComm:
                        num_PDMBSM_DualComm = len(Sub_id_list)
                    self.PDMBSM_DualComm = self.rnd.sample(Sub_id_list, num_PDMBSM_DualComm)

            if CF.Control['PDMMarketPenetration'] != None:
                num_PDM =  int(round(len(IDs) * (CF.Control['PDMMarketPenetration'] / 100.0)))
                if len(self.equip_DualPDMBSM) > 0:
                    Sub_id_list = [ID for ID in IDs if ID not in self.equip_DualPDMBSM]
                    if len(Sub_id_list) < num_PDM:
                        num_PDM = len(Sub_id_list)
                    self.equip_PDM = self.rnd.sample(Sub_id_list, num_PDM)
                else:
                    if len(IDs) < num_PDM:
                        num_PDM = len(IDs)
                    self.equip_PDM = self.rnd.sample(IDs, num_PDM)

                Sub_id_list = [ID for ID in self.equip_PDM]
                if CF.Control['PDMDSRCMarketPenetration'] != None:
                    num_PDM_DSRC = int(round(len(self.equip_PDM) * (CF.Control['PDMDSRCMarketPenetration'] / 100.00)))
                    self.PDM_DSRC = self.rnd.sample(Sub_id_list, num_PDM_DSRC)
                    Sub_id_list = [ID for ID in self.equip_PDM if ID not in self.PDM_DSRC]

                if CF.Control['PDMCellularMarketPenetration'] != None:
                    num_PDM_Cellular = int(round(len(self.equip_PDM) * (CF.Control['PDMCellularMarketPenetration'] / 100.00)))
                    if len(Sub_id_list) < num_PDM_Cellular:
                        num_PDM_Cellular = len(Sub_id_list)
                    self.PDM_Cellular = self.rnd.sample(Sub_id_list, num_PDM_Cellular)
                    Sub_id_list = [ID for ID in self.equip_PDM if ID not in self.PDM_Cellular and ID not in self.PDM_DSRC]

                if CF.Control['PDMDualCommMarketPenetration'] != None:
                    num_PDM_DualComm = int(round(len(self.equip_PDM) * (CF.Control['PDMDualCommMarketPenetration'] / 100.00)))
                    if len(Sub_id_list) < num_PDM_DualComm:
                        num_PDM_DualComm = len(Sub_id_list)
                    self.PDM_DualComm = self.rnd.sample(Sub_id_list, num_PDM_DualComm)

            if CF.Control['BSMMarketPenetration'] != None:
                num_BSM =  int(round(len(IDs) * (CF.Control['BSMMarketPenetration'] / 100.0)))
                if len(self.equip_PDM) > 0 or len(self.equip_DualPDMBSM) > 0:
                    Sub_id_list = [ID for ID in IDs if ID not in self.equip_PDM and ID not in self.equip_DualPDMBSM]
                    if len(Sub_id_list) < num_BSM:
                        num_BSM = len(Sub_id_list)
                    self.equip_BSM = self.rnd.sample(Sub_id_list, num_BSM)
                else:
                    if len(IDs) < num_BSM:
                        num_BSM = len(IDs)
                    self.equip_BSM = self.rnd.sample(IDs, num_BSM)
                Sub_id_list = [ID for ID in self.equip_BSM]
                if CF.Control['BSMDSRCMarketPenetration'] != None:
                    num_BSM_DSRC = int(round(len(self.equip_BSM) * (CF.Control['BSMDSRCMarketPenetration'] / 100.00)))
                    self.BSM_DSRC = self.rnd.sample(Sub_id_list, num_BSM_DSRC)
                    Sub_id_list = [ID for ID in self.equip_BSM if ID not in self.BSM_DSRC]

                if CF.Control['BSMCellularMarketPenetration'] != None:
                    num_BSM_Cellular = int(round(len(self.equip_BSM) * (CF.Control['BSMCellularMarketPenetration'] / 100.00)))
                    if len(Sub_id_list) < num_BSM_Cellular:
                        num_BSM_Cellular = len(Sub_id_list)
                    self.BSM_Cellular = self.rnd.sample(Sub_id_list, num_BSM_Cellular)
                    Sub_id_list = [ID for ID in self.equip_BSM if ID not in self.BSM_Cellular and ID not in self.BSM_DSRC]

                if CF.Control['BSMDualCommMarketPenetration'] != None:
                    num_BSM_DualComm = int(round(len(self.equip_BSM) * (CF.Control['BSMDualCommMarketPenetration'] / 100.00)))
                    if len(Sub_id_list) < num_BSM_DualComm:
                        num_BSM_DualComm = len(Sub_id_list)
                    self.BSM_DualComm = self.rnd.sample(Sub_id_list, num_BSM_DualComm)
            self.equip_vehicles = self.equip_PDM + self.equip_BSM + self.equip_DualPDMBSM

        elif (len(CF.Control['PDMVehicleIDs']) > 0) or (len(CF.Control['BSMVehicleIDs']) > 0) or (len(CF.Control['DualPDMBSMVehicleIDs']) > 0):

            if (len(CF.Control['DualPDMBSMVehicleIDs']) > 0):
                self.equip_DualPDMBSM = CF.Control['DualPDMBSMVehicleIDs']
                if (len(CF.Control['PDMBSMDSRCVehicleIDs']) > 0):
                    self.PDMBSM_DSRC = CF.Control['PDMBSMDSRCVehicleIDs']
                if (len(CF.Control['PDMBSMCellularVehicleIDs']) > 0):
                    self.PDMBSM_Cellular = CF.Control['PDMBSMCellularVehicleIDs']
                if (len(CF.Control['PDMBSMDualCommVehicleIDs']) > 0):
                    self.PDMBSM_DualComm = CF.Control['PDMBSMDualCommVehicleIDs']

            if (len(CF.Control['PDMVehicleIDs']) > 0):
                self.equip_PDM = CF.Control['PDMVehicleIDs']
                if (len(CF.Control['PDMDSRCVehicleIDs']) > 0):
                    self.PDM_DSRC = CF.Control['PDMDSRCVehicleIDs']
                if (len(CF.Control['PDMCellularVehicleIDs']) > 0):
                    self.PDM_Cellular = CF.Control['PDMCellularVehicleIDs']
                if (len(CF.Control['PDMDualCommVehicleIDs']) > 0):
                    self.PDM_DualComm = CF.Control['PDMDualCommVehicleIDs']

            if (len(CF.Control['BSMVehicleIDs']) > 0):
                self.equip_BSM = CF.Control['BSMVehicleIDs']
                if (len(CF.Control['BSMDSRCVehicleIDs']) > 0):
                    self.BSM_DSRC = CF.Control['BSMDSRCVehicleIDs']
                if (len(CF.Control['BSMCellularVehicleIDs']) > 0):
                    self.BSM_Cellular = CF.Control['BSMCellularVehicleIDs']
                if (len(CF.Control['BSMDualCommVehicleIDs']) > 0):
                    self.BSM_DualComm = CF.Control['BSMDualCommVehicleIDs']

            self.equip_vehicles = self.equip_PDM + self.equip_BSM + self.equip_DualPDMBSM

        #TODO see if there is a way to reset the iterator
        if not self.vissim_file:
            _infile = self.open_trajectory_file( self.vissim_file, CF.Control['TrajectoryFileName'])
        else:
            _infile = self.open_trajectory_file( self.vissim_file, CF.Control['TrajectoryFileName'],
                                                         skip_lines = line_skip )

        if CF.Control['AccelColumn'] != None:
            self.include_accel = True

        _lastbit = None
        self.total_len = 0
        for c, chunk in enumerate(_infile):

            if _lastbit is not None:
                chunk = pd.concat([chunk, _lastbit])

            if self.vissim_file:
                if (len(CF.Control['PDMVehicleTypes']) > 0) or \
                   (len(CF.Control['BSMVehicleTypes']) > 0) or \
                   (len(CF.Control['DualPDMBSMVehicleTypes']) > 0):
                        try:
                            chunk = chunk[['VehNr', 't', 'WorldX', 'WorldY', 'v', 'a', 'Type']]
                        except:
                            print('Error missing one of VISSIM key fields: VehNr, t, WorldX, WorldY, v, a, Type')
                            sys.exit(None)
                        chunk = chunk.rename(columns={'VehNr': 'vehicle_ID', 'v': 'speed', 't': 'time', 'WorldX': 'location_x',
                                       'WorldY': 'location_y', 'a': 'accel_instantaneous', 'Type': 'vehicle_type'})
                else:
                    try:
                        chunk = chunk[['VehNr', 't', 'WorldX', 'WorldY', 'v', 'a']]
                    except:
                        print('Error missing one of VISSIM key fields: VehNr, t, WorldX, WorldY, v, a')
                        sys.exit(None)
                    chunk = chunk.rename(columns={'VehNr': 'vehicle_ID', 'v': 'speed', 't': 'time', 'WorldX': 'location_x',
                                   'WorldY': 'location_y', 'a': 'accel_instantaneous',})
            else:
                if (len(CF.Control['PDMVehicleTypes']) > 0) or \
                   (len(CF.Control['BSMVehicleTypes']) > 0) or \
                   (len(CF.Control['DualPDMBSMVehicleTypes']) > 0):

                    if not self.include_accel:
                        chunk = chunk[[CF.Control['IDColumn'], CF.Control['TimeColumn'], CF.Control['XColumn'],
                                 CF.Control['YColumn'], CF.Control['SpdColumn'], CF.Control['TypeColumn']]]
                        chunk = chunk.rename(columns={
                            CF.Control['IDColumn']: 'vehicle_ID',
                            CF.Control['SpdColumn']: 'speed',
                            CF.Control['TimeColumn']: 'time',
                            CF.Control['XColumn']: 'location_x',
                            CF.Control['YColumn']: 'location_y',
                            CF.Control['TypeColumn']: 'vehicle_type'
                        })

                    else:

                        chunk = chunk[[CF.Control['IDColumn'], CF.Control['TimeColumn'], CF.Control['XColumn'],
                                 CF.Control['YColumn'], CF.Control['SpdColumn'], CF.Control['TypeColumn'],
                                 CF.Control['AccelColumn'] ]]

                        chunk = chunk.rename(columns={
                            CF.Control['IDColumn']: 'vehicle_ID',
                            CF.Control['SpdColumn']: 'speed',
                            CF.Control['TimeColumn']: 'time',
                            CF.Control['XColumn']: 'location_x',
                            CF.Control['YColumn']: 'location_y',
                            CF.Control['TypeColumn']: 'vehicle_type',
                            CF.Control['AccelColumn']: 'accel_instantaneous',
                        })


                else:

                    if not self.include_accel:

                        chunk = chunk[[CF.Control['IDColumn'], CF.Control['TimeColumn'], CF.Control['XColumn'],
                                 CF.Control['YColumn'], CF.Control['SpdColumn']]]
                        chunk = chunk.rename(columns={
                                CF.Control['IDColumn']: 'vehicle_ID',
                                CF.Control['SpdColumn']: 'speed',
                                CF.Control['TimeColumn']: 'time',
                                CF.Control['XColumn']: 'location_x',
                                CF.Control['YColumn']: 'location_y'
                        })
                    else:
                        chunk = chunk[[CF.Control['IDColumn'], CF.Control['TimeColumn'], CF.Control['XColumn'],
                                 CF.Control['YColumn'], CF.Control['SpdColumn'], CF.Control['AccelColumn']]]
                        chunk = chunk.rename(columns={
                                CF.Control['IDColumn']: 'vehicle_ID',
                                CF.Control['SpdColumn']: 'speed',
                                CF.Control['TimeColumn']: 'time',
                                CF.Control['XColumn']: 'location_x',
                                CF.Control['YColumn']: 'location_y',
                                CF.Control['AccelColumn']: 'accel_instantaneous',
                        })

            if (len(CF.Control['BSMVehicleTypes']) == 0) and (len(CF.Control['BSMVehicleIDs']) == 0) and \
                   (CF.Control['BSMMarketPenetration'] == None) and (CF.Control['DualPDMBSMMarketPenetration'] == None) \
                   and (len(CF.Control['DualPDMBSMVehicleTypes']) == 0) and (len(CF.Control['DualPDMBSMVehicleIDs']) == 0):
                    chunk = chunk[(chunk['time'] % 1 == 0)] #remove 1/10 Second values

            #Determine Equipped vehicles based on Vehicle Type
            if (len(CF.Control['PDMVehicleTypes']) > 0) or (len(CF.Control['BSMVehicleTypes']) > 0) or (len(CF.Control['DualPDMBSMVehicleTypes']) > 0):

                if (len(CF.Control['DualPDMBSMVehicleTypes']) > 0):
                    chunk_dualpdmbsm = chunk[chunk['vehicle_type'].isin(CF.Control['DualPDMBSMVehicleTypes'])]
                    self.equip_DualPDMBSM = list(set(self.equip_DualPDMBSM + list(set(chunk_dualpdmbsm['vehicle_ID'].tolist()))))

                    if (len(CF.Control['PDMBSMDSRCVehicleTypes']) > 0):
                        chunk_pdmbsm_dsrc = chunk_dualpdmbsm[chunk_dualpdmbsm['vehicle_type'].isin(CF.Control['PDMBSMDSRCVehicleTypes'])]
                        self.PDMBSM_DSRC = list(set(self.PDMBSM_DSRC + list(set(chunk_pdmbsm_dsrc['vehicle_ID'].tolist()))))

                    if (len(CF.Control['PDMBSMCellularVehicleTypes']) > 0):
                        chunk_pdmbsm_cellular = chunk_dualpdmbsm[chunk_dualpdmbsm['vehicle_type'].isin(CF.Control['PDMBSMCellularVehicleTypes'])]
                        self.PDMBSM_Cellular = list(set(self.PDMBSM_Cellular + list(set(chunk_pdmbsm_cellular['vehicle_ID'].tolist()))))

                    if (len(CF.Control['PDMBSMDualCommVehicleTypes']) > 0):
                        chunk_pdmbsm_dualcomm = chunk_dualpdmbsm[chunk_dualpdmbsm['vehicle_type'].isin(CF.Control['PDMBSMDualCommVehicleTypes'])]
                        self.PDMBSM_DualComm = list(set(self.PDMBSM_DualComm + list(set(chunk_pdmbsm_dualcomm['vehicle_ID'].tolist()))))

                if (len(CF.Control['PDMVehicleTypes']) > 0):
                    chunk_pdm = chunk[chunk['vehicle_type'].isin(CF.Control['PDMVehicleTypes'])]
                    self.equip_PDM = list(set(self.equip_PDM + list(set(chunk_pdm['vehicle_ID'].tolist()))))

                    if (len(CF.Control['PDMDSRCVehicleTypes']) > 0):
                        chunk_pdm_dsrc = chunk_pdm[chunk_pdm['vehicle_type'].isin(CF.Control['PDMDSRCVehicleTypes'])]
                        self.PDM_DSRC = list(set(self.PDM_DSRC + list(set(chunk_pdm_dsrc['vehicle_ID'].tolist()))))

                    if (len(CF.Control['PDMCellularVehicleTypes']) > 0):
                        chunk_pdm_cellular = chunk_pdm[chunk_pdm['vehicle_type'].isin(CF.Control['PDMCellularVehicleTypes'])]
                        self.PDM_Cellular = list(set(self.PDM_Cellular + list(set(chunk_pdm_cellular['vehicle_ID'].tolist()))))

                    if (len(CF.Control['PDMDualCommVehicleTypes']) > 0):
                        chunk_pdm_dualcomm = chunk_pdm[chunk_pdm['vehicle_type'].isin(CF.Control['PDMDualCommVehicleTypes'])]
                        self.PDM_DualComm = list(set(self.PDM_DualComm + list(set(chunk_pdm_dualcomm['vehicle_ID'].tolist()))))

                if (len(CF.Control['BSMVehicleTypes']) > 0):
                    chunk_bsm = chunk[chunk['vehicle_type'].isin(CF.Control['BSMVehicleTypes'])]
                    self.equip_BSM = list(set(self.equip_BSM +  list(set(chunk_bsm['vehicle_ID'].tolist()))))

                    if (len(CF.Control['BSMDSRCVehicleTypes']) > 0):
                        chunk_bsm_dsrc = chunk_bsm[chunk_bsm['vehicle_type'].isin(CF.Control['BSMDSRCVehicleTypes'])]
                        self.BSM_DSRC = list(set(self.BSM_DSRC + list(set(chunk_bsm_dsrc['vehicle_ID'].tolist()))))

                    if (len(CF.Control['BSMCellularVehicleTypes']) > 0):
                        chunk_bsm_cellular = chunk_bsm[chunk_bsm['vehicle_type'].isin(CF.Control['BSMCellularVehicleTypes'])]
                        self.BSM_Cellular = list(set(self.BSM_Cellular + list(set(chunk_bsm_cellular['vehicle_ID'].tolist()))))

                    if (len(CF.Control['BSMDualCommVehicleTypes']) > 0):
                        chunk_bsm_dualcomm = chunk_bsm[chunk_bsm['vehicle_type'].isin(CF.Control['BSMDualCommVehicleTypes'])]
                        self.BSM_DualComm = list(set(self.BSM_DualComm + list(set(chunk_bsm_dualcomm['vehicle_ID'].tolist()))))

                self.equip_vehicles = self.equip_PDM + self.equip_BSM + self.equip_DualPDMBSM

            chunk = chunk[chunk['vehicle_ID'].isin(self.equip_vehicles)]


            if len(chunk) > 0:
                chunk = chunk.sort('time')

                #If the data needs to be broken into multiple files
                if os.path.getsize(CF.Control['TrajectoryFileName']) > self.CHUNK_SIZE:
                    _last_tp = chunk.tail(1)['time'].values[0]
                    _lastbit = chunk[ chunk['time'] == _last_tp ]
                    chunk = chunk[ chunk['time'] != _last_tp ]

                _tmp_file = tmpfile.NamedTemporaryFile(delete=False)
                chunk.to_pickle(_tmp_file.name)
                self.temp_files.append(_tmp_file.name)

            self.total_len += len(chunk)


        self.equip_vehicles = sorted(self.equip_vehicles)

        self.DSRC_list = self.PDM_DSRC + self.BSM_DSRC + self.PDMBSM_DSRC
        self.cellular_list = self.PDM_Cellular + self.BSM_Cellular + self.PDMBSM_Cellular
        self.dualcomm_list = self.PDM_DualComm + self.BSM_DualComm + self.PDMBSM_DualComm

        if self.total_len == 0:
            print ('Error Vehicle IDs never found or trajectory file has no data')
            sys.exit(0)

        if CF.Control['OutputLevel'] > 0:
            logger.info("%s number of lines loaded" % (str(self.total_len)))

        if CF.Control['OutputLevel'] >= 1:
            logger.info ('Total number of equipped vehicle = %d' % (len(self.equip_vehicles)))
            logger.info ("Number of PDM vehicles transmitting via DSRC(%d), Cellular(%d), and DSRC or Cellular(%d)"
                   % (len(self.PDM_DSRC), len(self.PDM_Cellular ), len(self.PDM_DualComm)))
            logger.info ("Number of BSM vehicles transmitting via DSRC(%d), Cellular(%d), and DSRC or Cellular(%d)"
                   % (len(self.BSM_DSRC), len(self.BSM_Cellular), len(self.BSM_DualComm)))
            logger.info ("Number of Dual PDM-BSM vehicles transmitting DSRC(%d), Cellular(%d), and DSRC or Cellular(%d)"
                   % (len(self.PDMBSM_DSRC), len(self.PDMBSM_Cellular), len(self.PDMBSM_DualComm)))



    def read(self):
        for tmp_file in self.temp_files:
            df = pd.read_pickle(tmp_file)

            # print df.head(5)

            #Remove and VehicleID that are in the same time period
            df.drop_duplicates(cols=['vehicle_ID', 'time'], take_last=True, inplace=True)
            grps = df.groupby('time')
            for tp, grp in grps:
                yield tp, grp.sort('vehicle_ID')



#*************************************************************************
class Trajectories_Tests(unittest.TestCase):

    def setUp(self):
        from TCALoadControl import ControlFiles
        from numpy import arange
        import random

        r = random.Random()
        r.seed(1234)

        self.CF = ControlFiles('test.xml')

        self.CF.control_values['OutputLevel'][0] = 0

        self.CF.control_values['XColumn'][0] = 'x'
        self.CF.control_values['YColumn'][0] = 'y'
        self.CF.control_values['TimeColumn'][0] = 'time'
        self.CF.control_values['IDColumn'][0] = 'ID'
        self.CF.control_values['SpdColumn'][0] = 'spd'
        self.CF.control_values['TypeColumn'][0] = 'type'


        with open('test_csv_input_file_del_me.csv', 'wb') as fout:

            self.vehicles = sorted(['B856', 'C234', 'D098', 'E342', 'W908', 'P342', 'Q231', 'T932', 'P212', 'A093'])

            fout.write('ID,time,spd,x,y,type\n')
            for num in arange(0, 10.5, 0.5):

                for c, vehicle in enumerate(self.vehicles):
                    spd = r.randint(0,70) * 1.0
                    x = r.random()
                    y = r.random()

                    if c==9:
                        type_val = '3'
                    elif c>4:
                        type_val = '2'
                    else:
                        type_val = '1'

                    fout.write(vehicle + ',' + str(num)+ ',' + str(spd) + ',' + str(x)[0:5] + ',' + str(y)[0:5]  + ',' + type_val + '\n')

        with open('test_csv_input_file_del_me_with_acc.csv', 'wb') as fout:

            self.vehicles = sorted(['B856', 'C234', 'D098', 'E342', 'W908', 'P342', 'Q231', 'T932', 'P212', 'A093'])

            a_val = range(-4, 6, 1)

            fout.write('ID,time,spd,x,y,type,acc\n')
            for num in arange(0, 10.5, 0.5):

                for c, vehicle in enumerate(self.vehicles):
                    spd = r.randint(0,70) * 1.0
                    a = a_val[c] * 1.1
                    x = r.random()
                    y = r.random()

                    if c==9:
                        type_val = '3'
                    elif c>4:
                        type_val = '2'
                    else:
                        type_val = '1'

                    fout.write(vehicle + ',' + str(num)+ ',' + str(spd) + ',' + str(x)[0:5] + ',' + str(y)[0:5]
                               + ',' + type_val + ',' + str(a) + '\n')



        with open('test_vissim_input_file_del_me.fzp', 'wb') as fout:
           fout.write(r"""Vehicle Record

File:     c:\users\m28050\documents\projects\fhwa\tca\v_2 vissim\intersection.inp
Comment:
Date:     Monday, September 30, 2013 11:21:06 AM
VISSIM:   5.40-08 [38878]

VehNr  : Number of the Vehicle
v      : Speed [mph] at the end of the simulation step
Type   : Number of the Vehicle Type
t      : Simulation Time [s]
WorldX : World coordinate x (vehicle front end at the end of the simulation step)
WorldY : World coordinate y (vehicle front end at the end of the simulation step)

   VehNr;      v; Type;       t;    WorldX;    WorldY;      a;
       1;  32.18;    1;    54.8; -4925.8665; -2581.9891;  -2.32
       2;  32.33;    2;    55.0; -4928.7503; -2581.9898;   4.52
       3;  32.47;    2;    55.2; -4931.6471; -2581.9906;  13.23
       4;  32.62;    1;    55.4; -4934.5570; -2581.9913;   0.23
       5;  32.77;    1;    55.6; -4937.4800; -2581.9920;  -2.21
       6;  32.91;    2;    55.8; -4940.4160; -2581.9928;  -12.32
       7;  33.06;    3;    56.0; -4943.3651; -2581.9935;   0.44
       """)



    # @unittest.skip("testing skipping")
    def test_load_read_csv(self):

        self.CF.control_values['TrajectoryFileName'][0] = 'test_csv_input_file_del_me.csv'
        self.CF.control_values['BSMMarketPenetration'][0] = 20
        self.CF.control_values['BSMDSRCMarketPenetration'][0] = 50
        self.CF.control_values['BSMCellularMarketPenetration'][0] = 50
        self.CF.map_dictionary()

        trj = Trajectories()
        trj.load(self.CF)

        assert len(trj.equip_vehicles) == 2 # 20% of 10
        assert len(trj.equip_PDM) == 0
        assert len(trj.DSRC_list) == 1
        assert len(trj.cellular_list) == 1
        assert trj.DSRC_list[0] != trj.cellular_list[0]

        c = 0
        for tp, df in trj.read():
            c=c+1
        assert c == 21 # every 10th of a sec BSM

    # @unittest.skip("testing skipping")
    def test_load_read_csv_with_accel(self):

        self.CF.control_values['TrajectoryFileName'][0] = 'test_csv_input_file_del_me_with_acc.csv'
        self.CF.control_values['AccelColumn'][0] = 'acc'
        self.CF.control_values['BSMMarketPenetration'][0] = 20
        self.CF.control_values['BSMDSRCMarketPenetration'][0] = 50
        self.CF.control_values['BSMCellularMarketPenetration'][0] = 50
        self.CF.map_dictionary()

        trj = Trajectories()
        trj.load(self.CF)

        c = 0
        for tp, df in trj.read():
            if c==1:
                assert df.loc[12, 'accel_instantaneous'] == -2.2
            c=c+1
        assert c == 21 # every 10th of a sec BSM




    # @unittest.skip("testing skipping")
    def test_load_read_csv_by_IDs(self):

        self.CF.control_values['TrajectoryFileName'][0] = 'test_csv_input_file_del_me.csv'
        self.CF.control_values['PDMVehicleIDs'][0] = ['Q231']
        self.CF.control_values['PDMDSRCVehicleIDs'][0] = ['Q231']
        self.CF.map_dictionary()

        trj = Trajectories()
        trj.load(self.CF)

        c = 0
        for tp, df in trj.read():
            c=c+1
        assert c == 11 #Every 1 sec (PDM)
        assert len(trj.PDM_DSRC) == 1

    # @unittest.skip("testing skipping")
    def test_load_read_vissim(self):
        self.CF.control_values['TrajectoryFileName'][0] = 'test_vissim_input_file_del_me.fzp'
        self.CF.control_values['FileType'][0] = 'VISSIM'
        self.CF.control_values['PDMVehicleTypes'][0] = [1]
        self.CF.control_values['BSMVehicleTypes'][0] = [2]
        self.CF.control_values['PDMDSRCVehicleTypes'][0] = [1]
        self.CF.control_values['BSMDualCommVehicleTypes'][0] = [2]

        self.CF.map_dictionary()

        trj = Trajectories()
        trj.load(self.CF)

        assert len(trj.equip_vehicles) == 6
        assert trj.equip_PDM == [1, 4, 5]
        assert trj.equip_BSM == [2, 3, 6]
        assert trj.PDM_DSRC == [1, 4, 5]
        assert trj.BSM_DualComm == [2, 3, 6]

        c = 0
        for tp, df in trj.read():
            if c ==0:
                assert df['vehicle_ID'][0] == 1
                assert df['time'][0] == 54.8
            c=c+1
        assert c == 6

    # @unittest.skip("testing skipping")
    def test_mix_PDE_BSM_markpen(self):

        self.CF.control_values['TrajectoryFileName'][0] = 'test_csv_input_file_del_me.csv'
        self.CF.control_values['BSMMarketPenetration'][0] = 20
        self.CF.control_values['PDMMarketPenetration'][0] = 20
        self.CF.map_dictionary()

        trj = Trajectories()
        trj.load(self.CF)

        assert trj.equip_vehicles == ['C234', 'E342', 'P212', 'Q231']
        assert trj.equip_PDM == ['C234', 'P212']
        assert trj.equip_BSM == ['Q231', 'E342']

        c = 0
        for tp, df in trj.read():
            c=c+1
        assert c == 21 #every 10th of a sec

    # @unittest.skip("testing skipping")
    def test_mix_PDE_BSM_type(self):

        self.CF.control_values['TrajectoryFileName'][0] = 'test_csv_input_file_del_me.csv'
        self.CF.control_values['PDMVehicleTypes'][0] = [1]
        self.CF.control_values['BSMVehicleTypes'][0] = [2]
        self.CF.map_dictionary()

        trj = Trajectories()
        trj.load(self.CF)

        assert trj.equip_vehicles == self.vehicles[0:9] #all but last one which is type 3
        assert sorted(trj.equip_PDM) == self.vehicles[0:5] #first 5 vehicles
        assert sorted(trj.equip_BSM) == self.vehicles[5:9] #vehicle 6-8

        c = 0
        for tp, df in trj.read():
            c=c+1
        assert c == 21 #every 10th of a sec

    # @unittest.skip("testing skipping")
    def test_mix_PDE_BSM_type_equal(self):

        with open('test_csv_input_file_del_me.csv', 'a') as fout:
            fout.write('GGG1,10.0,34.2,23.4,2324.2,1\n')

        self.CF.control_values['TrajectoryFileName'][0] = 'test_csv_input_file_del_me.csv'
        self.CF.control_values['BSMMarketPenetration'][0] = 50
        self.CF.control_values['PDMMarketPenetration'][0] = 50
        self.CF.map_dictionary()

        trj = Trajectories()
        trj.load(self.CF)

        assert len(trj.equip_vehicles) == 11
        assert len(trj.equip_PDM) == 6
        assert len(trj.equip_BSM) == 5


    def tearDown(self):
        import os
        os.remove('test_csv_input_file_del_me_with_acc.csv')
        os.remove('test_csv_input_file_del_me.csv')
        os.remove('test_vissim_input_file_del_me.fzp')


if __name__ == '__main__':
    unittest.main()
