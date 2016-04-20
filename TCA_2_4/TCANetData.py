#standard
import unittest

#tca
from TCACore import logger

#RSE class for holding RSE information
class CLNetData:

    def __init__(self, unit_conversion = 1.0):
        """
        Intializes CLNetData module

        :param unit_conversion: The value used to convert input values to correct units if necessary
        """

        self.RSEList = {}
        self.RSEListLocations = {}
        self.SPOTList = {}
        self.SPOTListLocations = {}
        self.unit_conversion = unit_conversion
#-------------------------------------------------------------------------
    def SPOTLoad(self, filename, CV):
        """
        Reads in SPOT RSE file

        :param filename: The SPOT RSE filename
        :param CV: Dictionary of control file inputs
        :return: A list of errors if any occurred
        """

        errors = []

        #loading file
        if CV.Control["OutputLevel"] > 0:
            logger.info("Loading SPOT file: %s" % (filename))

        with open(filename, 'r') as f:
            header = f.readline()

            for line in f.readlines():

                try:
                    SPOTinfo = line.split(',')
                    SPOT = {}

                    SPOT["name"] = SPOTinfo[0]
                    SPOT["x"] = float(SPOTinfo[1]) * self.unit_conversion
                    SPOT["y"] = float(SPOTinfo[2]) * self.unit_conversion


                    self.SPOTList[SPOTinfo[0]] = SPOT # Add the entry to the master dictionary

                except:
                    errors.append("Error Reading in SPOT File line: %s" % line)

        if CV.Control["OutputLevel"] > 0:
            logger.info("Number of SPOT devices = %s" % (len(self.SPOTList)))

        return errors

#-------------------------------------------------------------------------
    def PrintRSE(self):
        """
        Prints out all RSE data

        """
        for name in self.RSEList.keys():
            print "%s(%.0f,%.0f)" % (name, self.RSEList[name]['x'], self.RSEList[name]['y'])

#-------------------------------------------------------------------------
    def RSELoad(self, filename, CV):

        """
        Reads in RSE file
        
        :param filename: The RSE filename
        :param CV: Dictionary of control file inputs
        :return: A list of errors if any occurred
        """
        errors = []

        #loading file
        if CV.Control["OutputLevel"] > 0:
            logger.info("Loading RSE file: %s" % (filename))

        with open(filename, 'r') as f:
            header = f.readline()

            for line in f.readlines():

                try:
                    RSEinfo = line.split(',')
                    RSE = {}

                    RSE["name"] = RSEinfo[0]
                    RSE["x"] = float(RSEinfo[1]) * self.unit_conversion
                    RSE["y"] = float(RSEinfo[2]) * self.unit_conversion
                    RSE["latency"] = 0.0
                    RSE["loss_rate"] = 0.0

                    if len(RSEinfo) > 3:
                        RSE["latency"] = int(RSEinfo[3])
                    if len(RSEinfo) > 4:
                        RSE["loss_rate"] = int(RSEinfo[4])

                    self.RSEList[RSEinfo[0]] = RSE 

                except:
                    errors.append("Error Reading in RSE File line: %s" % line)

        if CV.Control["OutputLevel"] > 0:
            logger.info("Number of RSE = %s" % (len(self.RSEList)))

        return errors

#*************************************************************************
class CLNetData_Tests(unittest.TestCase):


    def setUp(self):
        from TCALoadControl import ControlFiles

        self.CF = ControlFiles()
        self.CF.Control["OutputLevel"] = 0
        self.CF.Control["FileType"] = 'CSV'

        self.tmpname = 'testingRSE_delete_later.csv'

    def test_loading(self):

        netdata = CLNetData()

        with open(self.tmpname, 'wb') as tmp_f:
            tmp_f.write('Name,X,Y\n')
            for x in range(20):
                tmp_f.write('test' + str(x) + ',2,3\n')



        errors = netdata.RSELoad(self.tmpname, self.CF)
        assert len(errors) == 0
        assert len(netdata.RSEList.keys()) == 20

        assert netdata.RSEList['test2'] == {'y': 3.0, 'x': 2.0, 'loss_rate': 0.0, 'name': 'test2', 'latency': 0.0}


        with open(self.tmpname, 'a') as tmp_f:
            tmp_f.write('test21,4,3,A,3\n')

        errors = netdata.RSELoad(self.tmpname, self.CF)
        assert len(errors) == 1



    def tearDown(self):
        import os
        os.remove(self.tmpname)


if __name__ == '__main__':
    unittest.main()