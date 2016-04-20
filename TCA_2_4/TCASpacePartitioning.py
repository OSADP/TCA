
#standard
import unittest

#external
from scipy.spatial import cKDTree

from TCACore import Timer

class Location_Tree():

    def __init__(self, roadside_equipment, minrange):
        """
        Initializes Space Tree class

        :param road_side_equipment: List of device with x,y values
        :param minrange: minimum range for communication
        """

        self.roadside_equipment = roadside_equipment
        self.roadside_equipment_points = [(device['x'], device['y']) for device in roadside_equipment.values() ]

        self.roadside_equipment_points_rev_lookup = {}

        c = 0
        for equipment in roadside_equipment.keys():
            self.roadside_equipment_points_rev_lookup[c] =  equipment
            c +=1

        self.roadside_equipment_tree = cKDTree(self.roadside_equipment_points)
        self.minrange = minrange
        self.timer = Timer(enabled=True)


    def find_ranges(self, vech_data):

        self.vehicle_points = []
        self.vehicle_points_rev_lookup = {}

        c = 0
        for vech in vech_data:
            if vech is not None and  vech['DSRC_enabled']:
                self.vehicle_points.append((vech['location_x'], vech['location_y']))
                self.vehicle_points_rev_lookup[c] = vech['vehicle_ID']
                c +=1

        vehicles_in_range = {}
        if len(self.vehicle_points) > 0:
            self.timer.start('sp_tree_search_all')
            locs_points = self.roadside_equipment_tree.query_ball_point(self.vehicle_points, r=self.minrange )
            self.timer.stop('sp_tree_search_all')

            for i in range(len(locs_points)):
                vehicles_in_range[self.vehicle_points_rev_lookup[i]] = \
                                            [self.roadside_equipment_points_rev_lookup[c] for c in locs_points[i]]

        return vehicles_in_range




    def find_range(self, x_value, y_value):
        """
        Finds all device within a given range of the point

        :param x_value: x value of vehicle location
        :param y_value: y value of vehicle location
        :return: list of device name in range
        """

        #Find closest RSEs
        self.timer.start('sp_tree_search')
        locs_points = self.roadside_equipment_tree.query_ball_point([x_value, y_value], r=self.minrange )
        self.timer.stop('sp_tree_search')

        self.timer.start('sp_tree_mapping')
        #link RSE back to vehicles
        equipment_names = []

        #map RSE points back to RSE names
        for i in locs_points:
            for device in self.roadside_equipment.keys():
                if self.roadside_equipment_points[i] == (self.roadside_equipment[device]['x'], self.roadside_equipment[device]['y']):
                    equipment_names.append(device)
                    break

        self.timer.stop('sp_tree_mapping')
        return equipment_names


class Location_Tree_tests(unittest.TestCase):
    def setUp(self):
        pass

    def test_range(self):

        RSEs = { 'RSE1' : {'x':5, 'y':4},
                 'RSE2' : {'x':5, 'y':5},
                 'RSE3' : {'x':1, 'y':1},
                 'RSE4' : {'x':10, 'y':10},
                 'RSE5' : {'x':4, 'y':5},
        }
        minrange = 2.00

        RSE_tree = Location_Tree(RSEs, minrange)


        veh_data = {'location_x':5.0, 'location_y':5.0,}

        rse_info = RSE_tree.find_range(veh_data['location_x'], veh_data['location_y'])

        assert len(rse_info) == 3
        assert 'RSE1' in rse_info
        assert 'RSE2' in rse_info
        assert 'RSE5' in rse_info

    def test_ranges(self):

        RSEs = { 'RSE1' : {'x':5, 'y':4},
                 'RSE2' : {'x':5, 'y':5},
                 'RSE3' : {'x':1, 'y':1},
                 'RSE4' : {'x':10, 'y':10},
                 'RSE5' :  {'x':4, 'y':5},
        }

        veh_data = [{'vehicle_ID' :'V1', 'DSRC_enabled': True, 'location_x':5.0, 'location_y':5.0,},
                    {'vehicle_ID' :'V2', 'DSRC_enabled': True, 'location_x':1.0, 'location_y':4.0,},
                    {'vehicle_ID' :'V3', 'DSRC_enabled': False, 'location_x':6.0, 'location_y':3.0,},
                    {'vehicle_ID' :'V4', 'DSRC_enabled': False, 'location_x':4.0, 'location_y':5.0,},
                    {'vehicle_ID' :'V5', 'DSRC_enabled': True, 'location_x':1.0, 'location_y':1.0,}]

        RSE_tree = Location_Tree(RSEs, 2.0)

        veh_ranges = RSE_tree.find_ranges(veh_data)

        assert 'V3' not in veh_ranges.keys()
        assert 'V4' not in veh_ranges.keys()

        assert len(veh_ranges['V1']) == 3
        assert 'RSE1' in veh_ranges['V1']
        assert 'RSE2' in veh_ranges['V1']
        assert 'RSE5' in veh_ranges['V1']

        assert len(veh_ranges['V2']) == 0

        assert len(veh_ranges['V5']) == 1
        assert 'RSE3' in veh_ranges['V5']



#------------------------------------------------------------


if __name__ == '__main__':
     unittest.main()


