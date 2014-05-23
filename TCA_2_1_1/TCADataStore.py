#standard
import unittest
from datetime import datetime as dt
from warnings import simplefilter
simplefilter(action = "ignore", category = UserWarning)

#external
import numpy as np
import pandas as pd

#TCA
from TCACore import Timer


copy_fields = [
    'departed_network',
    'time_in_network',
    'vehicle_ID_buffer_empty',
    'vehicle_SS_buffer_empty',
    'SS_count_generated_by_vehicle',
    'SS_count_in_vehicle',
    'time_to_next_periodic',
    'distance_to_next_periodic',
    'time_motionless',
    'time_of_last_stop',
    'distance_of_last_stop',
    'time_stamp_of_ID',
    'permanent_PSN',
    'temp_PSN',
    'looking_for_start',
    'in_privacy_gap',
    'privacy_gap_start',
    'time_in_privacy_gap',
    'RSE_interaction',
    'PSN_counter_ID',
    'PSN_start_time',
    'PSN_start_distance',
    'PSN_distance_travelled',
    'PSN_change_ID',
    'distance_travelled_in_gap',
    'time_of_start_snapshot',
    'time_of_periodic_snapshot',
    'time_of_last_transmit',
    'cellular_enabled',
    'last_RSE_transmitted_to',
    'PDM_equipped',
    'BSM_equipped',
    ]

class DataStorage(object):
    """Class that holds all current Vehicle information"""
    # TODO: fix time_step values for BSMs
    def __init__(self, ids, PDM_list, BSM_list, time_step = 1):

        self.time_step = time_step
        self.start = True


        self.core_cols = [
            'time',
            'speed',
            'location_x',
            'location_y',]

        self.core_cols_vissim = [
            'PDM_equipped',
            'BSM_equipped',
            'cellular_enabled',]


        self.df = pd.DataFrame({
            'vehicle_ID' : ids,
            'active' : False,
            'time_in_network' : 0.0,
            'time_out_network' : 0.0,
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
            'permanent_PSN' : 0,
            'temp_PSN' : -1234,
            'looking_for_start' : False,
            'in_privacy_gap' : False,
            'privacy_gap_start' : 0,
            'time_in_privacy_gap' : 0.0,
            'distance_in_privacy_gap' : 0.0,
            'RSE_interaction' : False,
            'PSN_counter_ID' : 1,
            'PSN_start_time' : 0.0,
            'PSN_start_distance' : 0.0,
            'PSN_distance_travelled' : 0.0,
            'PSN_change_ID' : 0,
            'distance_travelled_in_gap' : 0.0,
            'new_distance' : 0.0,
            'location_x_last' : 0.0,
            'location_y_last' : 0.0,
            'time_last' : 0.0,
            'speed_last' : -30,
            'time': -5.0,
            'speed': 0.0,
            'location_x': 0.0,
            'location_y': 0.0,
            'time_of_start_snapshot' : 0,
            'time_of_periodic_snapshot' : 0,
            'time_of_last_transmit' : 0,
            'cellular_enabled' : False,
            'average_acceleration' : 0,
            'last_RSE_transmitted_to' : -1,
            'PDM_equipped' : False,
            'BSM_equipped' : False,
        })

        self.df = self.df.set_index(['vehicle_ID'], drop=False)
        self.df = self.df.sort('vehicle_ID')


        self.update_distances = [
                'distance_of_last_stop',
                'distance_to_next_periodic',
                'PSN_distance_travelled',
                'distance_travelled_in_gap',]

        self.df['PDM_equipped'][PDM_list] = True
        self.df['BSM_equipped'][BSM_list] = True

        self.runtimer = False

        self.timer = Timer()


    def update(self, tp, df, RandomGen, TCA_version = 'standalone'):

        if self.runtimer:
            self.timer.start('tbl_update_columns')

        #copy new data in
        new_ids = list(df['vehicle_ID'].unique())
        df = df.set_index(['vehicle_ID'], drop=False)

        #find Vehicles that this is the first time we see them
        new_ID_list = self.df.loc[new_ids][(self.df['location_y'] == 0)  & (self.df['location_x'] == 0)]

        self.df.loc[new_ids, self.core_cols] = np.float64(df.loc[new_ids, self.core_cols])

        if TCA_version != 'standalone':
            self.df.loc[new_ids, self.core_cols_vissim] = df.loc[new_ids, self.core_cols_vissim]

        if self.runtimer:
            self.timer.stop()
            self.timer.start('tbl_set_inactive')


        self.df['active'][new_ids] = True
        self.df['time_out_network'][new_ids] = 0

        self.df['time_out_network'][self.df.index - df.index] += self.time_step
        self.df['active'][((self.df['active'] == True) & (self.df['time_out_network'] > 3))] = False

        dis_index =  df.index - new_ID_list.index

        if self.runtimer:
             self.timer.stop()

        if len(dis_index) > 0:

            if self.runtimer:
                self.timer.start('tbl_calulate_distance')

            self.df['new_distance'][dis_index] = np.sqrt(
                           (self.df['location_y'][dis_index]
                            - self.df['location_y_last'][dis_index]) ** 2 +
                            (self.df['location_x'][dis_index]
                            - self.df['location_x_last'][dis_index]) ** 2)

            if self.runtimer:
                self.timer.stop()
                self.timer.start('tbl_set_distance')

            for col in self.update_distances:
                self.df[col][new_ids] = self.df['new_distance'][new_ids] + self.df[col][new_ids]


            if self.runtimer:
                self.timer.stop()
                self.timer.start('tbl_time_out_network')

            #update out of network information
            self.df['time_out_network'][(self.df['time']==tp)] = 0
            self.df['time_out_network'][(self.df['time']!=tp)] = \
                self.df['time_out_network'][(self.df['time']!=tp)] + self.time_step

            if self.runtimer:
                self.timer.stop()

        if self.runtimer:
            self.timer.start('tbl_last_value')

        self.df['location_x_last'] = self.df['location_x']
        self.df['location_y_last'] = self.df['location_y']
        if self.df["time_last"] is not 0:
            self.df['average_acceleration'] = (self.df['speed'] -
                self.df['speed_last'])/ (self.df['time'] - self.df['time_last'])
        self.df['speed_last'] = self.df['speed']
        self.df['time_last'] = self.df['time']
        self.start = False
        if self.runtimer:
            self.timer.stop()

        self.df['time_stamp_of_ID'][(self.df['temp_PSN'] == -1234) & (self.df['active'] == True)] = tp
        new_df = self.df['temp_PSN'][(self.df['temp_PSN'] == -1234) & (self.df['active'] == True)]
        for i in new_df.index:
            self.df['temp_PSN'][i] = RandomGen['psn']


class DataStorage_Tests(unittest.TestCase):

    def setUp(self):
        import random
        from TCALoadControl import ControlFiles

        r = random.Random()
        r.seed(1234)

        self.CF = ControlFiles()
        self.CF.map_dictionary()
        self.CF.Control['XColumn'] = 'x'
        self.CF.Control['YColumn'] = 'y'
        self.CF.Control['TimeColumn'] = 'time'
        self.CF.Control['IDColumn'] = 'ID'
        self.CF.Control['SpdColumn'] = 'spd'

        with open('test_delete_me_trajectory_file.csv', 'wb') as tst_tf:
            tst_tf.write('ID, time, Something, spd, x, y\n')
            for num in range(100):
                spd = r.randint(0,70) * 1.0
                x = r.random()
                y = r.random()
                tst_tf.write('A' + str(num) + ',' + str(num +4)  + ',Rock,' + str(spd) + ',' + str(x) + ',' + str(y) + '\n')

    def test_active_tbl(self):
        from TCAFileReader import Trajectories
        from TCARandom import Random_generator

        self.CF.Control['OutputLevel'] = 0
        self.CF.Control['PDMMarketPenetration'] = 20
        self.CF.Control['TrajectoryFileName'] = 'test_delete_me_trajectory_file.csv'

        RandomGen = Random_generator()
        RandomGen.add_generator_range('GapDistance', 0, 200)
        RandomGen.add_generator_range('GapTimeout', 0, 60)
        RandomGen.add_generator_range('psn', 0, 32767)  #range based on J2735
        RandomGen.add_generator_range('LossPercent', 1, 100)

        trj = Trajectories()
        trj.load(self.CF)

        tbl = DataStorage(trj.equip_vehicles, trj.equip_PDM, trj.equip_BSM)

        for tp, df in trj.read():
            tbl.update(tp, df, RandomGen)

        assert len(tbl.df) == 20

    def tearDown(self):
        import os
        os.remove('test_delete_me_trajectory_file.csv')



if __name__ == '__main__':
    unittest.main()
