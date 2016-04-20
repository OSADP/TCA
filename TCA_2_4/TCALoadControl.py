#standard

import time
import unittest
import os
import sys
import xml.etree.ElementTree as ET
from copy import deepcopy

#TCA
from TCACore import logger, curdir, control_values, strategy_values


class ControlFiles():
    """
    Call for reading and validating all Control Files
    """

    def __init__(self, control_file = 'TCA_input.xml', TCA_version = 'standalone' ):
        """
        Set all key default values for Control and Strategy file

        :param control_file: string of master control file
        :param TCA_version: string version of the TCA_version
        """
        self.control_values = deepcopy(control_values)
        self.strategy_values = deepcopy(strategy_values)

        self.control_file = control_file

        if sys.platform in ['win32']:
            if ':' in control_file:
                self.control_file = control_file
            else:
                self.control_file = curdir + control_file
        else:
            self.control_file = control_file


        self.TCA_version = TCA_version

        self.Control = {}
        self.Strategy = {}
        self.DIDC = {}



    def Error_count(self):
        """
        Counts the number of errors in control files

        :return count: integer with the number of errors
        """
        count = 0
        for key in self.control_values:
            if self.control_values[key][2] != '':
                # print self.control_values[key]
                count +=1
        for key in self.strategy_values:
            if self.strategy_values[key][2] != '':
                count +=1
               
        return count


    def map_dictionary(self):
        """
        changes 2 dimensional list to single

        """
        for key in self.control_values:
            self.Control[key] = self.control_values[key][0]

        for key in self.strategy_values:
            self.Strategy[key] = self.strategy_values[key][0]


    def Load_files(self):
        """
        Main method to read control files

        """
        self.Load_Control()
        if self.control_values["StrategyFile"][0]  != None:
            self.Load_Strategy()

        self.Create_input_summary_file()

        if self.Error_count()  >= 1.0:
            logger.error('There is an error in the input values.  Please check TCA_Input_Summary.csv for more information')
            sys.exit(0)
        self.map_dictionary()

    def int_check(self, value, key):
        """
        checks value to make sure they are integers.  if not reports error

        :param value: value of given input
        :param key: key name of input
        :return: value as int and string of error
        """
        try:
            int(value)
            return int(value), ''
        except:
            return None, 'Error: %s value must be an integer' % (key)


    def float_check(self, value, key):
        """
        checks value to make sure they are floats.  if not reports error

        :param value: value of the given input
        :param key: key name of input
        :return: value as float and string of error
        """
        try:
            float(value)
            return float(value), ''
        except:
            return None, 'Error: %s value must be a float' % (key)


    def file_check(self, value):
        """

        :param value: string value of the file
        :return:
        """
        if sys.platform in ['win32']:
            if ':' in value:
                return value
            else:
                return curdir + value
        else:
            return value


    def Load_Control(self):
        """
        Loads and checks control file values

        """
        try:
            tree = ET.parse(self.control_file)
            root = tree.getroot()
        except:
            if self.control_file != curdir + 'not a file.xml':
                logger.info("Error: cannot find or invalid format for control_values file %s" % self.control_file)
            raise

        for key, value in self.control_values.iteritems():

            if root.find(value[4]) != None:

                if value[3] == 'int':
                        self.control_values[key][0], self.control_values[key][2] = self.int_check(root.find(value[4]).text, key)
                elif value[3] == 'List_int':
                    self.control_values[key][0] = str(root.find(value[4]).text).split(',')
                    try:
                        self.control_values[key][0] =  [ int(i) for i in self.control_values[key][0]]
                    except:
                        pass

                elif value[3] == 'file':
                        self.control_values[key][0] = self.file_check(root.find(value[4]).text)
                elif value[3] == 'Upper':
                    self.control_values[key][0] = root.find(value[4]).text.upper()
                else:
                    self.control_values[key][0] = root.find(value[4]).text

                self.control_values[key][1] = 'User_Defined'


        if self.control_values["OutputLevel"][0] !=0:
            if self.control_file == "TCAinput.xml":
                logger.info("Using default file name: TCAinput.xml")
            logger.info("TCA Version 2.3 created by Noblis")
            logger.info("Start time %s" % (time.strftime('%X', time.localtime(time.time()))))
            logger.info("Loading control_values file %s" % (self.control_file))


        #Addtional Error checking
        if self.control_values["OutputLevel"][0] not in [0,1,2,3]:
            self.control_values["OutputLevel"][2] = 'Error: OutputLevel can only be values 0,1,2,3'

        if (self.control_values["PDMMarketPenetration"][0] < 0 or self.control_values["PDMMarketPenetration"][0] > 100) \
            and (self.control_values["PDMMarketPenetration"][0] != 0):
           self.control_values["PDMMarketPenetration"][2] = 'Error: PDMMarketPenetration is less than 0 or greater than 100'

        if (self.control_values["BSMMarketPenetration"][0] < 0 or self.control_values["BSMMarketPenetration"][0] > 100) \
            and (self.control_values["BSMMarketPenetration"][0] != 0):
           self.control_values["BSMMarketPenetration"][2] = 'Error: BSMMarketPenetration is less than 0 or greater than 100'

        if (self.control_values["PDMDSRCMarketPenetration"][0] < 0 or self.control_values["PDMDSRCMarketPenetration"][0] > 100) \
            and (self.control_values["PDMDSRCMarketPenetration"][0] != 0):
           self.control_values["PDMDSRCMarketPenetration"][2] = 'Error: PDMDSRCMarketPenetration is less than 0 or greater than 100'

        if (self.control_values["CAMMarketPenetration"][0] < 0 or self.control_values["CAMMarketPenetration"][0] > 100) \
            and (self.control_values["CAMMarketPenetration"][0] != 0):
           self.control_values["CAMMarketPenetration"][2] = 'Error: CAMMarketPenetration is less than 0 or greater than 100'

        if (self.control_values["SPOTMarketPenetration"][0] < 0 or self.control_values["SPOTMarketPenetration"][0] > 100) \
            and (self.control_values["SPOTMarketPenetration"][0] != 0):
           self.control_values["SPOTMarketPenetration"][2] = 'Error: SPOTMarketPenetration is less than 0 or greater than 100'

        if (self.control_values["PDMCellularMarketPenetration"][0] < 0 or self.control_values["PDMCellularMarketPenetration"][0] > 100) \
            and (self.control_values["PDMCellularMarketPenetration"][0] != None):
           self.control_values["PDMCellularMarketPenetration"][2] = 'Error: PDMCellularMarketPenetration is less than 0 or greater than 100'

        if (self.control_values["PDMDualCommMarketPenetration"][0] < 0 or self.control_values["PDMDualCommMarketPenetration"][0] > 100) \
            and (self.control_values["PDMDualCommMarketPenetration"][0] != None):
           self.control_values["PDMDualCommMarketPenetration"][2] = 'Error: PDMDualCommMarketPenetration is less than 0 or greater than 100'

        if (self.control_values["BSMDSRCMarketPenetration"][0] < 0 or self.control_values["BSMDSRCMarketPenetration"][0] > 100) \
            and (self.control_values["BSMDSRCMarketPenetration"][0] != None):
           self.control_values["BSMDSRCMarketPenetration"][2] = 'Error: BSMDSRCMarketPenetration is less than 0 or greater than 100'

        if (self.control_values["BSMCellularMarketPenetration"][0] < 0 or self.control_values["BSMCellularMarketPenetration"][0] > 100) \
            and (self.control_values["BSMCellularMarketPenetration"][0] != None):
           self.control_values["BSMCellularMarketPenetration"][2] = 'Error: BSMCellularMarketPenetration is less than 0 or greater than 100'

        if (self.control_values["BSMDualCommMarketPenetration"][0] < 0 or self.control_values["BSMDualCommMarketPenetration"][0] > 100) \
            and (self.control_values["BSMDualCommMarketPenetration"][0] != None):
           self.control_values["BSMDualCommMarketPenetration"][2] = 'Error: BSMDualCommMarketPenetration is less than 0 or greater than 100'

        if self.control_values["BSMMarketPenetration"][0] != 0 and self.control_values["PDMMarketPenetration"][0] != 0:
            if (self.control_values["BSMMarketPenetration"][0] + self.control_values["PDMMarketPenetration"][0]) > 100:
                self.control_values["BSMMarketPenetration"][2] = 'Error: BSM and PDM equipage market penetration is more than 100%'
                self.control_values["PDMMarketPenetration"][2] = 'Error: BSM and PDM equipage market penetration is more than 100%'

        if self.control_values["PDMMarketPenetration"][0] != 0:
            if (len(self.control_values["PDMDSRCVehicleTypes"][0]) > 0) or (len(self.control_values["PDMDSRCVehicleIDs"][0]) > 0) or \
                (len(self.control_values["PDMCellularVehicleTypes"][0]) > 0) or (len(self.control_values["PDMCellularVehicleIDs"][0]) > 0):
                    self.control_values["PDMDSRCVehicleTypes"][2] = 'Error: Must use ONLY MarketPenetration, VehicleTypes, or VehicleIDs'
                    self.control_values["PDMDSRCVehicleIDs"][2] = 'Error: Must use ONLY MarketPenetration, VehicleTypes, or VehicleIDs'
                    self.control_values["PDMCellularVehicleTypes"][2] = 'Error: Must use ONLY MarketPenetration, VehicleTypes, or VehicleIDs'
                    self.control_values["PDMCellularVehicleIDs"][2] = 'Error: Must use ONLY MarketPenetration, VehicleTypes, or VehicleIDs'

        if self.control_values["BSMMarketPenetration"][0] != 0:
            if (len(self.control_values["BSMDSRCVehicleTypes"][0]) > 0) or (len(self.control_values["BSMDSRCVehicleIDs"][0]) > 0) or \
                (len(self.control_values["BSMCellularVehicleTypes"][0]) > 0) or (len(self.control_values["BSMCellularVehicleIDs"][0]) > 0):
                    self.control_values["BSMDSRCVehicleTypes"][2] = 'Error: Must use ONLY MarketPenetration, VehicleTypes, or VehicleIDs'
                    self.control_values["BSMDSRCVehicleIDs"][2] = 'Error: Must use ONLY MarketPenetration, VehicleTypes, or VehicleIDs'
                    self.control_values["BSMCellularVehicleTypes"][2] = 'Error: Must use ONLY MarketPenetration, VehicleTypes, or VehicleIDs'
                    self.control_values["BSMCellularVehicleIDs"][2] = 'Error: Must use ONLY MarketPenetration, VehicleTypes, or VehicleIDs'

        if (self.TCA_version == 'standalone') and (self.control_values["FileType"][0] == 'CSV') and \
            ((self.control_values["XColumn"][0] == None) or (self.control_values["YColumn"][0] == None) or \
           (self.control_values["SpdColumn"][0] == None) or (self.control_values["IDColumn"][0] == None) or \
           (self.control_values["TimeColumn"][0] == None)):
                self.control_values["XColumn"][2] = 'Error: Missing either XColumn YColumn SpdColumn IDColumn or TimeColumn xml tag'
                self.control_values["YColumn"][2] = 'Error: Missing either XColumn YColumn SpdColumn IDColumn or TimeColumn xml tag'
                self.control_values["SpdColumn"][2] = 'Error: Missing either XColumn YColumn SpdColumn IDColumn or TimeColumn xml tag'
                self.control_values["IDColumn"][2] = 'Error: Missing either XColumn YColumn SpdColumn IDColumn or TimeColumn xml tag'
                self.control_values["TimeColumn"][2] = 'Error: Missing either XColumn YColumn SpdColumn IDColumn or TimeColumn xml tag'

        if (self.TCA_version == 'standalone') and (self.control_values["PDMMarketPenetration"][0] == 0) and \
           (self.control_values["PDMVehicleIDs"][0] == None) and (self.control_values["PDMVehicleTypes"][0] == None) and \
           (self.control_values["BSMVehicleIDs"][0] == None) and (self.control_values["BSMVehicleTypes"][0] == None) and \
           (self.control_values["BSMMarketPenetration"][0] == None) and (self.control_values["CAMMarketPenetration"][0] == 0) and \
            (self.control_values["CAMVehicleIDs"][0] == None) and (self.control_values["CAMVehicleTypes"][0] == None) and \
            (self.control_values["SPOTMarketPenetration"][0] == 0) and (self.control_values["SPOTVehicleIDs"][0] == None) and \
            (self.control_values["SPOTVehicleTypes"][0] == None) and (self.control_values["DualPDMBSMMarketPenetration"][0] == 0) and \
            (self.control_values["DualPDMBSMVehicleIDs"][0] == None) and (self.control_values["DualPDMBSMVehicleTypes"][0] == None):

            self.control_values["PDMMarketPenetration"][2] = 'Error: No vehicle equipage detected. Must select either include MarketPenetration, VehicleIDs, ' \
                                                    'or VehicleTypes to define equipped vehicles'
            self.control_values["BSMMarketPenetration"][2] = 'Error: No vehicle equipage detected. Must select either include MarketPenetration, VehicleIDs, ' \
                                                    'or VehicleTypes to define equipped vehicles'
            self.control_values["DualPDMBSMMarketPenetration"][2] = 'Error: No vehicle equipage detected. Must select either include MarketPenetration, VehicleIDs, ' \
                                                    'or VehicleTypes to define equipped vehicles'
            self.control_values["CAMMarketPenetration"][2] = 'Error: No vehicle equipage detected. Must select either include MarketPenetration, VehicleIDs, ' \
                                                    'or VehicleTypes to define equipped vehicles'
            self.control_values["SPOTMarketPenetration"][2] = 'Error: No vehicle equipage detected. Must select either include MarketPenetration, VehicleIDs, ' \
                                                    'or VehicleTypes to define equipped vehicles'

        if (self.TCA_version != 'standalone'):
            color_values = ['BSMTransColor','PDMPeriodicColor','PDMStopColor','PDMStartColor','PDMDSRCTransColor','PDMCellularTransColor','SpotBehaviorColor','SpotTravelColor',\
            'SpotTransColor','DualPDMBSMColor','PDMDefaultColor','BSMDefaultColor','DefaultColor']
            for color in color_values:
                if len(self.control_values[color][0]) != 3:
                    self.control_values[color][2] = 'Error: Vehicle color must be specified as a list of three integers RGB values'

    def Load_Strategy(self):
        """
        Load and checks strategy file values


        """
        if self.control_values['OutputLevel'][0] >= 1:
            logger.info("Loading strategy_values File %s" % (self.control_values["StrategyFile"][0]))

        try:
            tree = ET.parse(self.control_values["StrategyFile"][0])
            root = tree.getroot()
        except:
            if self.control_file != 'not a file.xml':
                logger.info("Error: cannot find or invalid format for strategy_values file %s" % self.control_values["StrategyFile"][0])
                print
            raise


        for key, value in self.strategy_values.iteritems():

            if root.find(value[4]) != None:

                if value[3] == 'int':
                        self.strategy_values[key][0], self.strategy_values[key][2] = self.int_check(root.find(value[4]).text, key)
                elif value[3] == 'file':
                    self.strategy_values[key][0]  = self.file_check(root.find(value[4]).text)
                elif value[3] == 'float':
                        self.strategy_values[key][0], self.strategy_values[key][2] = self.float_check(root.find(value[4]).text, key)
                else:
                    self.strategy_values[key][0] = root.find(value[4]).text

                self.strategy_values[key][1] = 'User_Defined'

   
    def Create_input_summary_file(self, file_name='TCA_Input_Summary.csv'):
         """
         Creates a summary input file

         :param file_name: string value for file
         """
         dir_path = os.path.dirname( os.path.realpath( __file__ ) )

         file_name = self.file_check(dir_path + '/' + file_name)

         with open(file_name, 'wb') as f_out:

            f_out.write('FILE,NAME,VALUE,XML_TAG,TYPE,ERRORS\n')

            for key in sorted(self.control_values):
                f_out.write('%s,%s,%s,%s,%s,%s\n' %
                           (self.control_file,
                            key,
                            self.control_values[key][0],
                            self.control_values[key][4],
                            self.control_values[key][1],
                            self.control_values[key][2],))

            for key in sorted(self.strategy_values):
                f_out.write('%s,%s,%s,%s,%s,%s\n' %
                           (self.control_values['StrategyFile'][0],
                            key,
                            self.strategy_values[key][0],
                            self.strategy_values[key][4],
                            self.strategy_values[key][1],
                            self.strategy_values[key][2],))


class LoadControlTest(unittest.TestCase):

    def setUp(self):

        with open('tca_delete_me_test_file_good.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8"?>
                    <ControlFile>
                        <OutputLevel>0</OutputLevel>
                        <Title>Test File</Title>
                        <Seed>342554</Seed>
                        <InputFiles>
                            <TrajectoryFile>
                                <FileType>csv</FileType>
                                <FileName>NCAR09_traj_0420.csv</FileName>
                                <CSVTrajectoryFileFields>
                                    <X>x_val</X>
                                    <Y>y_val</Y>
                                    <Time>time</Time>
                                    <ID>IDs</ID>
                                    <Speed>v</Speed>
                                </CSVTrajectoryFileFields>
                            </TrajectoryFile>
                            <RSELocationFile>RSE_locations.csv</RSELocationFile>
                            <StrategyFile>strategy_values.xml</StrategyFile>
                        </InputFiles>
                        <EquippedVehicles>
                            <PDMMarketPenetration>90</PDMMarketPenetration>
                            <SPOTMarketPenetration>10</SPOTMarketPenetration>
                            <PDMEquipped>
                                <DSRC>
                                    <MarketPenetration>50</MarketPenetration>
                                </DSRC>
                            </PDMEquipped>
                        </EquippedVehicles>
                        <OutputFiles>
                            <PDMTransFile>TCAout.csv</PDMTransFile>
                            <PDMAllFile>TCAoutALL.csv</PDMAllFile>
                            <BSMTransFile>TCAoutBSM.csv</BSMTransFile>
                        </OutputFiles>
                    </ControlFile>""")

        with open('tca_delete_me_test_file_good_vissim.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8"?>
                    <ControlFile>
                        <OutputLevel>0</OutputLevel>
                        <Title>Test File</Title>
                        <Seed>342554</Seed>
                        <InputFiles>
                            <TrajectoryFile>
                                <FileType>VISSIM</FileType>
                                <FileName>c:/VISSIM.fzp</FileName>
                            </TrajectoryFile>
                            <RSELocationFile>RSE_locations.csv</RSELocationFile>
                            <StrategyFile>strategy_values.xml</StrategyFile>
                        </InputFiles>
                        <EquippedVehicles>
                            <PDMVehicleTypes>1,2</PDMVehicleTypes>
                            <PDMEquipped>
                                <DSRC>
                                    <VehicleTypes>1</VehicleTypes>
                                </DSRC>
                                <Cellular>
                                    <VehicleTypes>2</VehicleTypes>
                                </Cellular>
                            </PDMEquipped>
                        </EquippedVehicles>
                    </ControlFile>""")

        with open('tca_delete_me_test_file_bad.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8"?>
                    <ControlFile>
                        <OutputLevel>0</OutputLevel>
                        <Title>Test File</Title>
                        <Seed>342554</Seed>
                        <InputFiles>
                            <TrajectoryFile>
                                <FileType>csv</FileType>
                                <FileName>NCAR09_traj_0420.csv</FileName>
                                <CSVTrajectoryFileFields>
                                    <X>x_val</X>
                                    <Time>time</Time>
                                    <ID>IDs</ID>
                                    <Speed>v</Speed>
                                </CSVTrajectoryFileFields>
                            </TrajectoryFile>
                            <RSELocationFile>RSE_locations.csv</RSELocationFile>
                        </InputFiles>
                        <EquippedVehicles>
                            <PDMMarketPenetration>110</PDMMarketPenetration>
                        </EquippedVehicles>
                        <OutputFiles>
                            <TransmittedSnapShotsFile>TCAout.csv</TransmittedSnapShotsFile>
                            <AllSnapShotsFile>TCAoutALL.csv</AllSnapShotsFile>
                            <TransmittedBSMFile>TCAoutBSM.csv</TransmittedBSMFile>
                        </OutputFiles>
                    </ControlFile>""")




        with open('tca_delete_me_test_file_bad2.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8"?>
                    <ControlFile>
                    <OutputLevel>0</OutputLevel>
                    </ControlFile>""")

        with open('tca_delete_me_test_file_bad3.xml', 'wb') as f_out:
            f_out.write("""<?xml version ="1.0" encoding="UTF-8"?>
                <ControlFile>
                        <OutputLevel>0</OutputLevel>
                        <Title>Test File</Title>
                        <Seed>342554</Seed>
                        <InputFiles>
                            <TrajectoryFile>
                                <FileType>csv</FileType>
                                <FileName>NCAR09_traj_0420.csv</FileName>
                                <CSVTrajectoryFileFields>
                                    <X>x_val</X>
                                    <Y>y_val</Y>
                                    <Time>time</Time>
                                    <ID>IDs</ID>
                                    <Speed>v</Speed>
                                </CSVTrajectoryFileFields>
                            </TrajectoryFile>
                            <RSELocationFile>RSE_locations.csv</RSELocationFile>
                            <StrategyFile>strategy_values.xml</StrategyFile>
                        </InputFiles>
                        <EquippedVehicles>
                            <PDMMarketPenetration>90</PDMMarketPenetration>
                            <PDMEquipped>
                                <DSRC>
                                    <VehicleIDs>1,2</VehicleIDs>
                                </DSRC>
                                <Cellular>
                                    <VehicleIDs>3</VehicleIDs>
                                </Cellular>
                            </PDMEquipped>
                        </EquippedVehicles>
                        <OutputFiles>
                            <PDMTransFile>TCAout.csv</PDMTransFile>
                            <PDMAllFile>TCAoutALL.csv</PDMAllFile>
                            <BSMTransFile>TCAoutBSM.csv</BSMTransFile>
                        </OutputFiles>
                    </ControlFile>""")

    def test_load_good(self):
        CF = ControlFiles('tca_delete_me_test_file_good.xml')
        CF.Load_Control()
        assert CF.Error_count() == 0
        assert CF.control_values["PDMMarketPenetration"][0] == 90
        assert CF.control_values["SPOTMarketPenetration"][0] == 10
        assert CF.control_values["RSELocationFile"][0] == curdir + 'RSE_locations.csv'
        assert CF.control_values["YColumn"][0] == 'y_val'
        assert CF.control_values["PDMDSRCMarketPenetration"][0] == 50

    def test_load_good_vissim(self):
        CF = ControlFiles('tca_delete_me_test_file_good_vissim.xml')
        CF.Load_Control()
        assert CF.Error_count() == 0
        assert CF.control_values["FileType"][0] == 'VISSIM'
        assert CF.control_values["TrajectoryFileName"][0] == 'c:/VISSIM.fzp'
        assert CF.control_values["PDMVehicleTypes"][0] == [1,2]
        assert CF.control_values["PDMDSRCVehicleTypes"][0] == [1]
        assert CF.control_values["PDMCellularVehicleTypes"][0] == [2]


    def test_load_bad(self):
        CF = ControlFiles('tca_delete_me_test_file_bad.xml')
        CF.Load_Control()
        assert CF.Error_count() == 6
        assert  CF.control_values["YColumn"][2] !=''
        assert  CF.control_values["PDMMarketPenetration"][2] !=''

    def test_load_bad2(self):

        CF = ControlFiles('tca_delete_me_test_file_bad2.xml')
        CF.Load_Control()
        assert CF.Error_count() == 5


    def test_load_bad3(self):
        CF = ControlFiles('tca_delete_me_test_file_bad3.xml')
        CF.Load_Control()
        assert CF.control_values["PDMDSRCVehicleIDs"] != ''
        assert CF.control_values["PDMCellularVehicleTypes"] != ''

    def test_load_bad4(self):
        try:
            CF = ControlFiles('not a file.xml')
            CF.Load_Control()
            assert False
        except:
            assert True


    def tearDown(self):
        os.remove('tca_delete_me_test_file_bad3.xml')
        os.remove('tca_delete_me_test_file_bad2.xml')
        os.remove('tca_delete_me_test_file_bad.xml')
        os.remove('tca_delete_me_test_file_good_vissim.xml')
        os.remove('tca_delete_me_test_file_good.xml')


#*************************************************************************
class LoadStrategyTest(unittest.TestCase):

    def setUp(self):

        with open('test_control_delete_me.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
                <ControlFile>
                <OutputLevel>0</OutputLevel>
                <InputFiles>
                    <TrajectoryFile>
                        <CSVTrajectoryFileFields>
                            <X>x-ft</X>
                            <Y>y-ft</Y>
                            <Time>secs</Time>
                            <ID>veh</ID>
                            <Speed>speed (mph)</Speed>
                        </CSVTrajectoryFileFields>
                        <EquippedVehicles>
                            <PDMMarketPenetration>90</PDMMarketPenetration>
                            <PDMEquipped>
                                <DSRC>
                                    <MarketPenetration>90</MarketPenetration>
                                </DSRC>
                                <Cellular>
                                    <MarketPenetration>10</MarketPenetration>
                                </Cellular>
                                <DualComm>
                                    <MarketPenetration>10</MarketPenetration>
                                </DualComm>
                            </PDMEquipped>
                        </EquippedVehicles>
                    </TrajectoryFile>
                    <StrategyFile>Strategy_cellular.xml</StrategyFile>
                </InputFiles>
                </ControlFile>
            """)

        with open('tca_delete_me_test_strategy_good.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
                    <strategy_values>
                      <Title>J2735 Noblis Modified strategy_values</Title>
                    <Inputs>
                     <PDM>
                     <PSNStrategy>
                      <TimeBetweenPSNSwitches>120</TimeBetweenPSNSwitches>
                      <DistanceBetweenPSNSwitches>3281</DistanceBetweenPSNSwitches>
                      <RSEFlag>0</RSEFlag>
                      <Gap>0</Gap>
                      </PSNStrategy>
                     <StopStartStrategy>
                      <strategy_values>1</strategy_values>
                      <StopThreshold>5</StopThreshold>
                      <StopLag>15</StopLag>
                      <StartThreshold>10</StartThreshold>
                      <MultipleStops>0</MultipleStops>
                      </StopStartStrategy>
                     <PeriodicStrategy>
                      <strategy_values>1</strategy_values>
                      <LowSpeedThreshold>20</LowSpeedThreshold>
                      <ShortSpeedinterval>6</ShortSpeedinterval>
                      <HighSpeedThreshold>60</HighSpeedThreshold>
                      <LongSpeedInterval>20</LongSpeedInterval>
                      <MaxDeltaSpeed>0.10</MaxDeltaSpeed>
                      </PeriodicStrategy>
                     <BufferStrategy>
                      <TotalCapacity>30</TotalCapacity>
                      <SSRetention>4</SSRetention>
                      </BufferStrategy>
                      <GapInformation>
                      <MinTime>3</MinTime>
                      <MaxTime>13</MaxTime>
                      <MinDistance>164</MinDistance>
                      <MaxDistance>820</MaxDistance>
                      </GapInformation>
                      </PDM>
                      <DSRC>
                     <RSEInformation>
                      <MinRSERange>492</MinRSERange>
                      <MaxRSERange>492</MaxRSERange>
                      <TimeoutRSE>200</TimeoutRSE>
                      <MinNumberofPDMSStoTransmitViaDSRC>2</MinNumberofPDMSStoTransmitViaDSRC>
                      <RSEReports>1</RSEReports>
                      </RSEInformation>
                      </DSRC>
                      <BSM>
                        <BrakeThreshold>-0.4</BrakeThreshold>
                        </BSM>
                      </Inputs>
                      </strategy_values>""")

        with open('tca_delete_me_test_file_bad.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
                        <strategy_values>
                          <Title>J2735 Noblis Modified strategy_values</Title>
                        <Inputs>
                        <PDM>
                         <PSNStrategy>
                          <TimeBetweenPSNSwitches>120</TimeBetweenPSNSwitches>
                          <DistanceBetweenPSNSwitches>3281</DistanceBetweenPSNSwitches>
                          <RSEFlag>0</RSEFlag>
                          <Gap>0</Gap>
                          </PSNStrategy>
                         <StopStartStrategy>
                          <strategy_values>1</strategy_values>
                          <StopThreshold>5</StopThreshold>
                          <StopLag>15</StopLag>
                          <StartThreshold>10</StartThreshold>
                          </StopStartStrategy>
                         <PeriodicStrategy>
                          <strategy_values>1</strategy_values>
                          <LowSpeedThreshold>20</LowSpeedThreshold>
                          <ShortSpeedInterval>A</ShortSpeedInterval>
                          <HighSpeedThreshold>60</HighSpeedThreshold>
                          <LongSpeedInterval>20</LongSpeedInterval>
                          <MaxDeltaSpeed>0.10</MaxDeltaSpeed>
                          </PeriodicStrategy>
                         <BufferStrategy>
                          <TotalCapacity>30</TotalCapacity>
                          <SSRetention>4</SSRetention>
                          </BufferStrategy>
                         <GapInformation>
                          <MinTime>3</MinTime>
                          <MaxTime>13</MaxTime>
                          <MinDistance>164</MinDistance>
                          <MaxDistance>820</MaxDistance>
                          </GapInformation>
                          </PDM>
                          <DSRC>
                         <RSEInformation>
                          <MinRSERange>492.0</MinRSERange>
                          <MaxRSERange>492</MaxRSERange>
                          <TimeoutRSE>200</TimeoutRSE>
                          <RSEReports>1</RSEReports>
                          </RSEInformation>
                          </DSRC>
                          </Inputs>
                          </strategy_values>""")

        with open('tca_delete_me_celluar_test_file_bad.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
        <Strategy>
          <Title>J2735 Noblis Modified Strategy</Title>
          <Inputs>
            <PDM>
             <PSNStrategy>
               <!--  Time between PSN Switches in Seconds  -->
               <TimeBetweenPSNSwitches>120</TimeBetweenPSNSwitches>
               <!--  Distance between PSN in feet   -->
               <DistanceBetweenPSNSwitches>3281</DistanceBetweenPSNSwitches>
               <!--  If Last RSE transmitted to is Included in Snapshot output 0-false 1-true -->
               <RSEFlag>0</RSEFlag>
             <!--
            If PSN Privacy gap is used:
            0 - No Gaps used
            1 - Rollover Gaps used (PSN changes if max time/distance is met)
            TODO: Add node to change rollover strategy options.
          -->
          <Gap>0</Gap>
        </PSNStrategy>
        <StopStartStrategy>
             <!--
            Stop/Start Strategy can be:
            1 - Max Time and Speed (both time and speed triggers start/stop)
            2 - Max Distance or time (either distance traveled or time motionless triggers start/stop)
          -->
          <Strategy>1</Strategy>
          <!--  Time threshold in seconds that is required to create a stop  -->
          <StopThreshold>5</StopThreshold>
          <!--  Time in seconds that must pass before a 2nd stop snapshot can be taken  -->
          <StopLag>15</StopLag>
             <!--  Speed in mph that a vechicle must have before a start snapshot can be taken
           -->
           <StartThreshold>10</StartThreshold>
             <!--  Can more than one SS in a row be taken 0-false 1-true
           -->
           <MultipleStops>0</MultipleStops>
         </StopStartStrategy>
         <PeriodicStrategy>
             <!--
            Periodic Strategy can be:
            1 - Speed Interpolation (Periodic SS taken based on Speed value)
            2 - Speed Exceptions (Periodic SS taken based on change in Speed)
          -->
          <Strategy>1</Strategy>
          <!--  Starting low speed threshold in mph that starts interpolation strategy 1 only  -->
          <LowSpeedThreshold>20</LowSpeedThreshold>
          <!--  Starting short time in seconds threshold that starts interpolation strategy 1 only  -->
          <ShortSpeedInterval>6</ShortSpeedInterval>
          <!--  Starting high speed threshold in mph that starts interpolation strategy 1 only  -->
          <HighSpeedThreshold>60</HighSpeedThreshold>
          <!--  Starting Long time in seconds threshold that starts interpolation strategy 1 only  -->
          <LongSpeedInterval>20</LongSpeedInterval>
          <!--  Percentage change in speed strategy 2 only  -->
          <MaxDeltaSpeed>0.10</MaxDeltaSpeed>
        </PeriodicStrategy>
        <BufferStrategy>
         <!--  Total size of the buffer  -->
         <TotalCapacity>30</TotalCapacity>
             <!--
            Buffer Retention Strategy can be:
            1 - FIFO
            2 - Every other SnapShot
            3 - Every other plus keep first and last ID
            4 - Every other plus save oldest SS
          -->
          <SSRetention>4</SSRetention>
        </BufferStrategy>
        <GapInformation>
         <!--  Min time in seconds for random generation of gap   -->
         <MinTime>3</MinTime>
         <!--  Max time in seconds for random generation of gap  -->
         <MaxTime>13</MaxTime>
         <!--  Min Distance in feet for random generation of gap  -->
         <MinDistance>164</MinDistance>
         <!--  Max Distance in feet for random generation of gap  -->
         <MaxDistance>820</MaxDistance>
        </GapInformation>
        </PDM>
        <DSRC>
        <RSEInformation>
         <!--  Min range for communication to RSE in feet  -->
         <MinRSERange>492</MinRSERange>
         <!--  Max range for communication to RSE in feet  -->
         <MaxRSERange>492</MaxRSERange>
         <!--  Timeout gap in seconds for RSE interaction  -->
         <TimeoutRSE>200</TimeoutRSE>
         <!--  Number of SS transmitted at a time.    -->
         <MinNumberofPDMSStoTransmitViaDSRC>1</MinNumberofPDMSStoTransmitViaDSRC>
         <!--  Number of times vehicle can transmit to RSE (0 value all of the time)  -->
         <RSEReports>1</RSEReports>
        </RSEInformation>
        </DSRC>
        </Inputs>
     </Strategy>""")

    def test_load_strategy(self):
        CF = ControlFiles('test_control_delete_me.xml')
        CF.Load_Control()
        assert  CF.Error_count() == 0
        CF.control_values['StrategyFile'][0] = curdir + 'tca_delete_me_test_strategy_good.xml'
        CF.Load_Strategy()

        assert CF.Error_count() == 0
        assert CF.strategy_values["StopThreshold"][0] == 5
        assert CF.strategy_values["StartThreshold"][0] == 10
        assert CF.strategy_values["GapMinDistance"][0] == 164
        assert CF.strategy_values["BrakeThreshold"][0] == -0.4

    def test_load_bad_strategy(self):
        CF = ControlFiles('test_control_delete_me.xml')
        CF.Load_Control()
        assert  CF.Error_count() == 0
        CF.control_values['StrategyFile'][0] = curdir + 'tca_delete_me_test_file_bad.xml'
        CF.Load_Strategy()
        assert  CF.Error_count() == 2
        assert CF.strategy_values["ShortSpeedInterval"][2] != ''
        assert CF.strategy_values["MinRSERange"][2] != ''


    def test_cellular_regions(self):
        CF = ControlFiles('test_control_delete_me.xml')
        CF.Load_Control()
        assert  CF.Error_count() == 0
        CF.control_values['StrategyFile'][0] = curdir + 'tca_delete_me_celluar_test_file_bad.xml'
        CF.Load_Strategy()

    def test_load_bad2_strategy(self):
        try:
            CF = ControlFiles('not a file.xml')
            CF.Load_Control()
            assert False
        except:
            assert True

    def test_write_outputs_strategy(self):
        CF = ControlFiles('test_control_delete_me.xml')
        CF.Load_Control()
        CF.control_values['StrategyFile'][0] = curdir + 'tca_delete_me_test_file_bad.xml'
        CF.Load_Strategy()
        assert CF.Error_count() == 2
        CF.Create_input_summary_file()

    def tearDown(self):
        import os
        os.remove('test_control_delete_me.xml')
        os.remove('tca_delete_me_test_strategy_good.xml')
        os.remove('tca_delete_me_test_file_bad.xml')
        os.remove('tca_delete_me_celluar_test_file_bad.xml')

#*************************************************************************
# class LoadDIDCTest(unittest.TestCase):

#     def setUp(self):
#         with open('test_DIDC_good.xml', 'wb') as f_out:
#             f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
#                             <DIDC>
#                                 <Title>DIDC Parameter File</Title>
#                                 <TransmissionThreshold>4</TransmissionThreshold>
#                                 <Periodic>
#                                     <Mean>300</Mean>
#                                 </Periodic>
#                                 <Turning>
#                                     <YawrateThreshold>5.0</YawrateThreshold>
#                                 </Turning>
                                
#                             </DIDC>
#                             """)

#         with open('test_DIDC_bad.xml', 'wb') as f_out:
#             f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
#                             <DIDC>
#                                 <Title>DIDC Parameter File</Title>
#                                 <TransmissionThreshold>Four</TransmissionThreshold>
#                                 <Periodic>
#                                     <Mean>300</Mean>
#                                 </Periodic>
#                                 <Turning>
#                                     <YawrateThreshold>Five</YawrateThreshold>
#                                 </Turning>

#                             </DIDC>
#                             """)

#     def test_load_good_file(self):
#         CF = ControlFiles()
#         CF.control_values['DIDCParametersFile'][0] = curdir + 'test_DIDC_good.xml'

#         assert CF.Error_count() == 0

#     def test_load_bad_file(self):
#         CF = ControlFiles()
#         CF.control_values['DIDCParametersFile'][0] = 'test_DIDC_bad.xml'

#         assert CF.Error_count() == 2
#     def tearDown(self):
#         import os
#         os.remove('test_DIDC_good.xml')
#         os.remove('test_DIDC_bad.xml')


if __name__ == '__main__':
    unittest.main()
    # inputf = "TCAinput.xml"
    # CF = ControlFiles(inputf)
    # CF.Load_Control()
    # CF.Load_Regions()