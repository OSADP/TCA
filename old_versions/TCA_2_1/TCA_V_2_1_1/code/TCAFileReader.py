#standard
import os
import random as rnd
import sys
import tempfile as tmpfile
import unittest

#external
import pandas as pd

class Trajectories(object):
    """Core class for reading vehicles trajectories"""

    def __init__(self, CHUNK_SIZE = 3000000):
        self.CHUNK_SIZE = CHUNK_SIZE
        self.temp_files = []
        self.rnd = rnd.Random()
        self.rnd.seed(3)

        self.equip_PDM = []
        self.equip_BSM = []

    def __del__(self):
        for tmp in self.temp_files:
            os.remove(tmp)

    def open_trajectory_file(self, file_type, filename, skip_lines = 1, ):

        if file_type == 'CSV':
             try:
                return pd.read_csv(filename,
                              iterator=True,
                              chunksize=self.CHUNK_SIZE,
                              skipinitialspace=True,
                              index_col=False,
                              )
             except:
                print 'Error: reading csv file.  Please check the format of the file'
                raise

        elif file_type == 'VISSIM':
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
                print 'Error: VISSIM fzp file does not have all required fields of: VehNr, t, WorldX, WorldY, and v'
                raise


#---------------------------------------------------------------
    def load(self, CF):

        if CF.Control['FileType'] == 'VISSIM':
            line_skip = 0
            with open(CF.Control['TrajectoryFileName']) as in_f:
                line = in_f.readline()
                while 'VehNr;' not in line:
                    line = in_f.readline()
                    line_skip += 1



        if CF.Control['OutputLevel'] >=1:
            print 'Loading %s Size %2.2f MB' % (CF.Control['TrajectoryFileName'].split('/')[-1],
                                                (os.path.getsize(CF.Control['TrajectoryFileName']) * 7.6294e-6))

        #Determine Market Penetration
        if (CF.Control['PDMMarketPenetration'] != None) or (CF.Control['BSMMarketPenetration'] != None):

           if CF.Control['FileType'] == 'CSV':
                _infile = self.open_trajectory_file( CF.Control['FileType'], CF.Control['TrajectoryFileName'])
           elif CF.Control['FileType']  == 'VISSIM':
                _infile = self.open_trajectory_file( CF.Control['FileType'], CF.Control['TrajectoryFileName'],
                                                     skip_lines = line_skip )
           IDs = []

           #Determine Equipped Vehicles based on MarkPenetration
           for chunk in _infile:

               if CF.Control['FileType']  == 'VISSIM':
                   IDs = IDs + list(chunk['VehNr'].unique())
               else:
                   IDs = IDs + list(chunk[CF.Control['IDColumn']].unique())

           if CF.Control['PDMMarketPenetration'] != None:
                num_PDM =  int(round(len(IDs) * (CF.Control['PDMMarketPenetration'] / 100.0)))
                self.equip_PDM = self.rnd.sample(IDs, num_PDM)

           if CF.Control['BSMMarketPenetration'] != None:
                num_BSM =  int(round(len(IDs) * (CF.Control['BSMMarketPenetration'] / 100.0)))
                if len(self.equip_PDM) > 0 :
                    Sub_id_list = [ID for ID in IDs if ID not in self.equip_PDM]
                    if len(Sub_id_list) < num_BSM:
                        num_BSM = len(Sub_id_list)
                    self.equip_BSM = self.rnd.sample(Sub_id_list, num_BSM)
                else:
                    if len(IDs) < num_BSM:
                        num_BSM = len(IDs)
                    self.equip_BSM = self.rnd.sample(IDs, num_BSM)

           self.equip_vehicles = self.equip_PDM + self.equip_BSM

        if (len(CF.Control['PDMVehicleIDs']) > 0) or (len(CF.Control['BSMVehicleIDs']) > 0):

            if (len(CF.Control['PDMVehicleIDs']) > 0):
                self.equip_PDM = CF.Control['PDMVehicleIDs']
            if (len(CF.Control['BSMVehicleIDs']) > 0):
                self.equip_BSM = CF.Control['BSMVehicleIDs']

            self.equip_vehicles = self.equip_PDM + self.equip_BSM


        #TODO see if there is a way to reset the iterator
        if CF.Control['FileType'] == 'CSV':
            _infile = self.open_trajectory_file( CF.Control['FileType'], CF.Control['TrajectoryFileName'])
        elif CF.Control['FileType'] == 'VISSIM':
            _infile = self.open_trajectory_file( CF.Control['FileType'], CF.Control['TrajectoryFileName'],
                                                         skip_lines = line_skip )

        _lastbit = None
        self.total_len = 0
        for c, chunk in enumerate(_infile):

            if _lastbit is not None:
                chunk = pd.concat([chunk, _lastbit])

            if CF.Control['FileType'] == 'VISSIM':
                if (len(CF.Control['PDMVehicleTypes']) > 0) or (len(CF.Control['BSMVehicleTypes']) > 0):
                    chunk = chunk[['VehNr', 't', 'WorldX', 'WorldY', 'v', 'Type']]
                    chunk = chunk.rename(columns={'VehNr': 'vehicle_ID', 'v': 'speed', 't': 'time', 'WorldX': 'location_x',
                                   'WorldY': 'location_y', 'Type': 'vehicle_type'})
                else:
                    chunk = chunk[['VehNr', 't', 'WorldX', 'WorldY', 'v']]
                    chunk = chunk.rename(columns={'VehNr': 'vehicle_ID', 'v': 'speed', 't': 'time', 'WorldX': 'location_x',
                                   'WorldY': 'location_y'})
            else:
                if (len(CF.Control['PDMVehicleTypes']) > 0) or (len(CF.Control['BSMVehicleTypes']) > 0):
                    chunk = chunk[[CF.Control['IDColumn'], CF.Control['TimeColumn'], CF.Control['XColumn'],
                             CF.Control['YColumn'], CF.Control['SpdColumn'], CF.Control['TypeColumn']]]
                    chunk = chunk.rename(columns={
                            CF.Control['IDColumn']: 'vehicle_ID',
                            CF.Control['SpdColumn']: 'speed',
                            CF.Control['TimeColumn']: 'time',
                            CF.Control['XColumn']: 'location_x',
                            CF.Control['YColumn']: 'location_y',
                            CF.Control['TypeColumn']: 'vehicle_type'})
                else:
                    chunk = chunk[[CF.Control['IDColumn'], CF.Control['TimeColumn'], CF.Control['XColumn'],
                             CF.Control['YColumn'], CF.Control['SpdColumn']]]
                    chunk = chunk.rename(columns={
                            CF.Control['IDColumn']: 'vehicle_ID',
                            CF.Control['SpdColumn']: 'speed',
                            CF.Control['TimeColumn']: 'time',
                            CF.Control['XColumn']: 'location_x',
                            CF.Control['YColumn']: 'location_y'})

            if (len(CF.Control['BSMVehicleTypes']) == 0) and (len(CF.Control['BSMVehicleIDs']) == 0) and \
                   (CF.Control['BSMMarketPenetration'] == None):
                    chunk = chunk[(chunk['time'] % 1 == 0)] #remove 1/10 Second values

            #Determine Equipped vehicles based on Vehicle Type
            if (len(CF.Control['PDMVehicleTypes']) > 0) or (len(CF.Control['BSMVehicleTypes']) > 0):

                if (len(CF.Control['PDMVehicleTypes']) > 0):
                    chunk_pdm = chunk[chunk['vehicle_type'].isin(CF.Control['PDMVehicleTypes'])]
                    self.equip_PDM = list(set(self.equip_PDM +  list(set(chunk_pdm['vehicle_ID'].tolist()))))

                if (len(CF.Control['BSMVehicleTypes']) > 0):
                    chunk_bsm = chunk[chunk['vehicle_type'].isin(CF.Control['BSMVehicleTypes'])]
                    self.equip_BSM = list(set(self.equip_BSM +  list(set(chunk_bsm['vehicle_ID'].tolist()))))

                self.equip_vehicles = self.equip_PDM + self.equip_BSM

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

        if self.total_len == 0:
            print 'Error Vehicle IDs never found or trajectory file has no data'
            sys.exit(0)

        if CF.Control['OutputLevel'] >=1:
            print "%s number of lines loaded" % (str(self.total_len))


    def read(self):
        for tmp_file in self.temp_files:
            df = pd.read_pickle(tmp_file)

            #Remove and VehicleID that are in the same time period
            df.drop_duplicates(cols=['vehicle_ID', 'time'], take_last=True, inplace=True)
            grps = df.groupby('time')
            for tp, grp in grps:
                yield tp, grp.sort('vehicle_ID')



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

   VehNr;      v; Type;       t;    WorldX;    WorldY;
       1;  32.18;    1;    54.8; -4925.8665; -2581.9891;
       2;  32.33;    2;    55.0; -4928.7503; -2581.9898;
       3;  32.47;    2;    55.2; -4931.6471; -2581.9906;
       4;  32.62;    1;    55.4; -4934.5570; -2581.9913;
       5;  32.77;    1;    55.6; -4937.4800; -2581.9920;
       6;  32.91;    2;    55.8; -4940.4160; -2581.9928;
       7;  33.06;    3;    56.0; -4943.3651; -2581.9935; """)



    def test_load_read_csv(self):

        self.CF.control_values['TrajectoryFileName'][0] = 'test_csv_input_file_del_me.csv'
        self.CF.control_values['BSMMarketPenetration'][0] = 20
        self.CF.map_dictionary()

        trj = Trajectories()
        trj.load(self.CF)

        assert len(trj.equip_vehicles) == 2 # 20% of 10
        assert len(trj.equip_PDM) == 0

        c = 0
        for tp, df in trj.read():
            c=c+1
        assert c == 21 # every 10th of a sec BSM

    def test_load_read_csv_by_IDs(self):

        self.CF.control_values['TrajectoryFileName'][0] = 'test_csv_input_file_del_me.csv'
        self.CF.control_values['PDMVehicleIDs'][0] = ['Q231']
        self.CF.map_dictionary()

        trj = Trajectories()
        trj.load(self.CF)

        c = 0
        for tp, df in trj.read():
            c=c+1
        assert c == 11 #Every 1 sec (PDM)


    def test_load_read_vissim(self):

        self.CF.control_values['TrajectoryFileName'][0] = 'test_vissim_input_file_del_me.fzp'
        self.CF.control_values['FileType'][0] = 'VISSIM'
        self.CF.control_values['PDMVehicleTypes'][0] = [1]
        self.CF.control_values['BSMVehicleTypes'][0] = [2]

        self.CF.map_dictionary()

        trj = Trajectories()
        trj.load(self.CF)

        assert len(trj.equip_vehicles) == 6
        assert trj.equip_PDM == [1, 4, 5]
        assert trj.equip_BSM == [2, 3, 6]

        c = 0
        for tp, df in trj.read():
            if c ==0:
                assert df['vehicle_ID'] == 1
                assert df['time'] == 54.8
            c=c+1
        assert c == 6

    def test_mix_PDE_BSM_markpen(self):

        self.CF.control_values['TrajectoryFileName'][0] = 'test_csv_input_file_del_me.csv'
        self.CF.control_values['BSMMarketPenetration'][0] = 20
        self.CF.control_values['PDMMarketPenetration'][0] = 20
        self.CF.map_dictionary()

        trj = Trajectories()
        trj.load(self.CF)

        assert trj.equip_vehicles == ['C234','D098','E342','P342']
        assert trj.equip_PDM == ['C234','E342']
        assert trj.equip_BSM == ['D098','P342']

        c = 0
        for tp, df in trj.read():
            c=c+1
        assert c == 21 #every 10th of a sec

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
        os.remove('test_csv_input_file_del_me.csv')
        os.remove('test_vissim_input_file_del_me.fzp')




if __name__ == '__main__':
    unittest.main()

