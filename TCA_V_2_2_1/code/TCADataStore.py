#standard
import unittest
from datetime import datetime as dt
from warnings import simplefilter
simplefilter(action = "ignore", category = UserWarning)

#external
import numpy as np
import pandas as pd

#TCA
from TCACore import Timer, logger

class DataStorage(object):
    """Class that holds all current Vehicle information"""
    def __init__(self, ids, Regions=None, PDM_list=None, BSM_list=None, DualPDMBSM_list=None, DSRC_list=None, Cellular_list=None,
                 DualComm_list=None, accel_included =  False, time_step = 1):

        self.time_step = time_step
        self.start = True

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


        self.core_cols_simulation = [
            'PDM_equipped',
            'BSM_equipped',
            'cellular_enabled',
            'DSRC_enabled',
            'dual_enabled',
            ]


        self.df = pd.DataFrame({
            'vehicle_ID' : ids,
            'active' : False,
            'vehicle_type' : None,
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
            'temp_PSN' : -1234,
            'looking_for_start' : False,
            'in_privacy_gap' : False,
            'privacy_gap_start' : 0,
            'PSN_time_to_end_gap' : 0.0,
            'distance_in_privacy_gap' : 0.0,
            'PSN_start_time' : 0.0,
            'PSN_start_distance' : 0.0,
            'PSN_distance_to_change' : 0.0,
            'PSN_change_ID' : 0,
            'PSN_distance_to_end_of_gap' : 0.0,
            'PSN_time_to_end_of_PSN' : 0.0,
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
            'DSRC_enabled' : False,
            'cellular_enabled' : False,
            'dual_enabled' : False,
            'average_acceleration' : 0.0,
            'accel_instantaneous' : 0.0,
            'last_RSE_transmitted_to' : -1,
            'PDM_equipped' : False,
            'BSM_equipped' : False,
            'dsrc_transmit_pdm' : False,
            'dsrc_transmit_bsm' : False,
            'brake_status' : '0000',
            'brake_pressure' : 0.0,
            'hard_braking' : 0,
            'sent_percent' : 0,
        })

        if Regions is not None:
            for Event in Regions.Event_titles:
                self.df[Event] = -9999

        self.df = self.df.set_index(['vehicle_ID'], drop=False)
        self.df = self.df.sort('vehicle_ID')

        if DualComm_list != None:
            self.df['dual_enabled'][DualComm_list] = True
        if PDM_list != None:
            self.df['PDM_equipped'][PDM_list] = True
        if BSM_list != None:
            self.df['BSM_equipped'][BSM_list] = True
        if Cellular_list != None:
            self.df['cellular_enabled'][Cellular_list] = True
        if DSRC_list != None:
            self.df['DSRC_enabled'][DSRC_list] = True
        if DualPDMBSM_list != None:
            self.df['PDM_equipped'][DualPDMBSM_list] = True
            self.df['BSM_equipped'][DualPDMBSM_list] = True


        self.timer = Timer(enabled=True)

    #-------------------------------------------------------------------------
    def copy_cols(self, new_ids, df):
        self.df.loc[df.index, df.columns] = df


    #-------------------------------------------------------------------------
    def update(self, tp, df, RandomGen, CF, TCA_version = 'standalone', time_step = 0.1):

        self.time_step = time_step

        self.timer.start('tbl_pull_new_ids')

        #copy new data in
        df = df.set_index(['vehicle_ID'], drop=False)

        self.timer.stop()
        self.timer.start('tbl_add_new ids')

        #find Vehicles that this is the first time we have see them
        df_tmp = self.df.loc[df.index]
        new_ID_list = df_tmp[(self.df['location_y'] == 0) & (self.df['location_x'] == 0)]

        self.df['location_x_last'] = self.df['location_x']
        self.df['location_y_last'] = self.df['location_y']

        self.timer.stop()
        self.timer.start('tbl_update_columns')

        self.df.loc[df.index, df.columns] = df

        if TCA_version != 'standalone':
            self.df.loc[df.index, self.core_cols_simulation] = df.loc[df.index, self.core_cols_simulation]

        self.timer.stop()
        self.timer.start('tbl_set_inactive')

        self.df['active'][df.index] = True
        self.df['time_out_network'][df.index] = 0

        self.df['time_out_network'][self.df.index - df.index] += 1
        self.df['total_time_in_network'][(self.df['active'])] += self.time_step

        self.df['active'][((self.df['active'] == True) & (self.df['time_out_network'] > 2))] = False

        dis_index =  df.index - new_ID_list.index

        self.timer.stop()

        if len(dis_index) > 0:

            self.timer.start('tbl_calculate_distance')

            self.df['new_distance'][dis_index] = np.sqrt(
                           (self.df['location_y'][dis_index]
                            - self.df['location_y_last'][dis_index]) ** 2 +
                            (self.df['location_x'][dis_index]
                            - self.df['location_x_last'][dis_index]) ** 2) 

            self.df['total_dist_traveled'] += self.df['new_distance']
            self.timer.stop()
            self.timer.start('tbl_set_distance')


            self.timer.stop()
            self.timer.start('tbl_time_out_network')

            #update out of network information
            self.df['time_out_network'][(self.df['time']==tp)] = 0
            self.df['time_out_network'][(self.df['time']!=tp)] = \
                self.df['time_out_network'][(self.df['time']!=tp)] + self.time_step

            self.timer.stop()

        self.timer.start('tbl_last_value')

        if self.df["time_last"] is not 0:
            self.df['average_acceleration'] = (self.df['speed'] -
                self.df['speed_last'])/ (self.df['time'] - self.df['time_last'])
        self.df['speed_last'] = self.df['speed']
        self.df['time_last'] = self.df['time']
        self.df['dsrc_transmit_bsm'] = False
        self.df['dsrc_transmit_pdm'] = False
        self.start = False
        self.timer.stop()


        new_df = self.df['temp_PSN'][(self.df['temp_PSN'] == -1234) & (self.df['active'] == True)]
        for i in new_df.index:
            self.df['temp_PSN'][i] = RandomGen['psn']
            self.df['PSN_distance_to_change'][i] =  self.df['total_dist_traveled'][i]  + CF.Strategy["DistanceBetweenPSNSwitches"]
            self.df['PSN_time_to_end_of_PSN'][i] = tp + CF.Strategy['TimeBetweenPSNSwitches']


#*************************************************************************
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
        RandomGen.add_generator_int('GapDistance', 0, 200)
        RandomGen.add_generator_int('GapTimeout', 0, 60)
        RandomGen.add_generator_int('psn', 0, 32767)  #range based on J2735
        RandomGen.add_generator_int('LossPercent', 1, 100)
        R = None

        trj = Trajectories()
        trj.load(self.CF)

        tbl = DataStorage(trj.equip_vehicles, R, trj.equip_PDM, trj.equip_BSM, trj.equip_DualPDMBSM, \
            trj.DSRC_list, trj.cellular_list, trj.dualcomm_list)

        for tp, df in trj.read(False):
            tbl.update(tp, df, RandomGen, self.CF)

        assert len(tbl.df) == 20

    def tearDown(self):
        import os
        os.remove('test_delete_me_trajectory_file.csv')



if __name__ == '__main__':
    unittest.main()
