#standard
import unittest
import math
#from collections import OrderedDict
from random import uniform

#external
import pandas as pd
from scipy.spatial import KDTree



def Find_RSE_range(df, RSEs, minrange):

    sub_df = df[['vehicle_ID', 'location_x', 'location_y']]


    tree = KDTree(sub_df[['location_x', 'location_y']].values)
    rse_points = list(RSEs.RSEList.values())
    locs_index = tree.query_ball_point(rse_points, r=minrange)

    #link RSE back to vehicles
    rse_vehicles = {}
    for c, RSE in enumerate(RSEs.RSEList.keys()):
        if len(locs_index[c]) > 0:
            vlist = sub_df.iloc[locs_index[c]]['vehicle_ID'].tolist()
            rse_vehicles[RSE] = vlist
        else:
            rse_vehicles[RSE] = []

    return rse_vehicles


#*************************************************************************
class BufferContentCheck(unittest.TestCase):
    def setUp(self):
        pass

    def test_whole(self):
        minrange = 4.00
        num_vehicles = 10000
        num_RSE = 30

        # Vehicles_loc = {}
        # for x in range (num_vehicles):
        #     Vehicles_loc[x] = (uniform(0, 200), uniform(0, 200))
        # df =  pd.DataFrame({
        #                'Vid' : ['V' + str(x) for x in  Vehicles_loc.keys()],
        #                'x' : [Vehicles_loc[x][0] for x in Vehicles_loc],
        #                'y' : [Vehicles_loc[x][1] for x in Vehicles_loc],
        #                })
        # df =  df.set_index(['Vid'], drop=False)

        # RSEs = {}
        # for x in range(num_RSE):
        #     RSEs['RSE' + str(x)] = (uniform(0, 200), uniform(0, 200))
        # #RSEs = OrderedDict({'RSE' + str(x):(uniform(0, 200), uniform(0, 200)) for x in range(num_RSE)})

        # rse_info = Find_RSE_range(df, RSEs, minrange)




if __name__ == '__main__':
    unittest.main()

