#standard
import unittest

#RSE class for holding RSE information
class CLNetData:

    def __init__(self):
        self.RSEList = {}

#-------------------------------------------------------------------------
#print out all RSE data
    def PrintRSE(self):
        for name in self.RSEList.keys():
            print "%s(%.0f,%.0f)" % (name, self.RSEList[name]['x'], self.RSEList[name]['y'])

#-------------------------------------------------------------------------
#reset the RSE Values
    def ResetRSE(self):

        for name in self.RSEList.keys():
            self.RSEList[name]["range"] = 0
            self.RSEList[name]["inrange"] = 0
            self.RSEList[name]["time"] = -3600
            self.RSEList[name]["interacttime"] = -3600
            self.RSEList[name]["interactcount"] = 0

#-------------------------------------------------------------------------
#reads in RSE file
    def RSELoad(self, filename, CV):

        errors = []

        #loading file
        if CV.Control["OutputLevel"] > 0:
            print "Loading RSE file: %s" % (filename)

        with open(filename, 'r') as f:

            for line in f.readlines()[1:]: #skip header line

                try:
                # Expects to find name, latitude, longitude, x (feet), and y (feet) in CSV file
                    NM, x, y = line.split(',')
                except:
                    errors.append("Error Reading in RSE File line: %s" % line)

                RSE = dict() #Create new RSE class object

                try:
                    RSE["x"] = float(x)
                    RSE["y"] = float(y)
                    RSE["name"] = NM
                except:
                    errors.append("Error in RSE File line : %s" % line)

                RSE["range"] = {}
                RSE["inrange"] = {}
                RSE["time"] = {}
                RSE["interacttime"] = {}
                RSE["interactcount"] = {}
                self.RSEList[NM] = RSE # Add the entry to the dictionary

        if CV.Control["OutputLevel"] > 0:
            print "Number of RSE = %s" % (len(self.RSEList))

        return errors

#*************************************************************************

class CLNetData_Tests(unittest.TestCase):


    def setUp(self):
        from TCACore import ControlVars

        self.CV = ControlVars()
        self.CV.Control["OutputLevel"] = 0

        self.tmpname = 'testingRSE_delete_later.csv'

    def test_loading(self):

        netdata = CLNetData()

        with open(self.tmpname, 'wb') as tmp_f:
            tmp_f.write('Name,X,Y\n')
            for x in range(20):
                tmp_f.write('test' + str(x) + ',2,3\n')

        errors = netdata.RSELoad(self.tmpname, self.CV)
        assert len(errors) == 0
        assert len(netdata.RSEList.keys()) == 20

        netdata.RSEList['test2']['interactcount'] = 100
        netdata.RSEList['test2']['time'] = 300
        netdata.ResetRSE()
        assert netdata.RSEList['test2']['interactcount'] == 0
        assert netdata.RSEList['test2']['time'] == -3600

        with open(self.tmpname, 'a') as tmp_f:
            tmp_f.write('test21,4,3,A,3\n')


        errors = netdata.RSELoad(self.tmpname, self.CV)
        assert len(errors) == 1



    def tearDown(self):
        import os
        os.remove(self.tmpname)




if __name__ == '__main__':
    unittest.main()