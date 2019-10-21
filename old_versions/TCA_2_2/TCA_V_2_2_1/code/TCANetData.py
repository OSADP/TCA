#standard
import unittest

#tca
from TCACore import logger

#RSE class for holding RSE information
class CLNetData:

    def __init__(self):
        self.RSEList = {}
        self.RSEListLocations = {}

#-------------------------------------------------------------------------
#print out all RSE data
    def PrintRSE(self):
        for name in self.RSEList.keys():
            print "%s(%.0f,%.0f)" % (name, self.RSEList[name]['x'], self.RSEList[name]['y'])

#-------------------------------------------------------------------------
#reads in RSE file
    def RSELoad(self, filename, CV):

        errors = []

        #loading file
        if CV.Control["OutputLevel"] > 0:
            logger.info("Loading RSE file: %s" % (filename))

        with open(filename, 'r') as f:
            header = f.readline()
            # splitline = header.split(',')

            for line in f.readlines():

                try:
                    RSEinfo = line.split(',')
                    RSE = {}

                    RSE["name"] = RSEinfo[0]
                    if CV.Control["FileType"] == 'VISSIM':
                        RSE["x"] = float(RSEinfo[1]) * 100 / 2.54 / 12      #Convert meters to feet
                        RSE["y"] = float(RSEinfo[2]) * 100 / 2.54 / 12      #Convert meters to feet
                    else:
                        RSE["x"] = float(RSEinfo[1])
                        RSE["y"] = float(RSEinfo[2])
                    RSE["latency"] = 0.0
                    RSE["loss_rate"] = 0.0
                    
                    if len(RSEinfo) > 3:
                        RSE["latency"] = int(RSEinfo[3])
                    if len(RSEinfo) > 4:
                        RSE["loss_rate"] = int(RSEinfo[4])

                    self.RSEList[RSEinfo[0]] = (RSE['x'], RSE['y'],RSE["latency"],RSE["loss_rate"]) # Add the entry to the master dictionary
                    self.RSEListLocations[RSEinfo[0]] = (RSE['x'], RSE['y'])                        # Add the entry to the locations (x,y) only dictionary for range finding tree

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

        assert netdata.RSEList['test2'] == (2.0, 3.0, 0.0, 0.0)


        with open(self.tmpname, 'a') as tmp_f:
            tmp_f.write('test21,4,3,A,3\n')

        errors = netdata.RSELoad(self.tmpname, self.CF)        
        assert len(errors) == 1



    def tearDown(self):
        import os
        os.remove(self.tmpname)


if __name__ == '__main__':
    unittest.main()