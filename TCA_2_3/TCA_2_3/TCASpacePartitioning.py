
#standard
import unittest

#external
from scipy.spatial import KDTree


class Location_Tree():

    def __init__(self, roadside_equipment, minrange):
        """
        Initializes Space Tree class

        :param road_side_equipment: List of device with x,y values
        :param minrange: minimum range for communication
        """

        self.roadside_equipment = roadside_equipment
        self.roadside_equipment_points = [(device['x'], device['y']) for device in roadside_equipment.values() ]
        self.roadside_equipment_tree = KDTree(self.roadside_equipment_points)
        self.minrange = minrange


    def Find_range(self, x_value, y_value):
        """
        Finds all device within a given range of the point

        :param x_value: x value of vehicle location
        :param y_value: y value of vehicle location
        :return: list of device name in range
        """

        #Find closest RSEs
        locs_points = self.roadside_equipment_tree.query_ball_point([x_value, y_value], r=self.minrange )

        #link RSE back to vehicles
        equipment_names = []

        #map RSE points back to RSE names
        for i in locs_points:
            for device in self.roadside_equipment.keys():
                if self.roadside_equipment_points[i] == (self.roadside_equipment[device]['x'], self.roadside_equipment[device]['y']):
                    equipment_names.append(device)
                    break

        return equipment_names


class Location_Tree_tests(unittest.TestCase):
    def setUp(self):
        pass

    def test_range(self):

        RSEs = { 'RSE1' : {'x':5, 'y':4},
                 'RSE2' : {'x':5, 'y':5},
                 'RSE3' : {'x':1, 'y':1},
                 'RSE4' : {'x':10, 'y':10},
                 'RSE5' :  {'x':4, 'y':5},
        }
        minrange = 2.00

        RSE_tree = Location_Tree(RSEs, minrange)


        veh_data = {'location_x':5.0, 'location_y':5.0,}

        rse_info = RSE_tree.Find_range(veh_data['location_x'], veh_data['location_y'])

        assert len(rse_info) == 3
        assert 'RSE1' in rse_info
        assert 'RSE2' in rse_info
        assert 'RSE5' in rse_info





if __name__ == '__main__':
    unittest.main()


