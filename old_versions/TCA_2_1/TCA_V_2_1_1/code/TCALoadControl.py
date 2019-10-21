#standard
import xml.etree.ElementTree as ET
import time
import unittest
import os
import sys

class ControlFiles():

    def __init__(self, control_file = 'TCA_input.xml', TCA_version = 'standalone' ):

        self.control_file = control_file
        self.TCA_version = TCA_version

        #Tuple for default value, value type, errors, data_chk, xml_tag
        self.control_values = {
            'OutputLevel' : [1, 'Default', '', 'int', 'OutputLevel'],
            'Title' : ['', 'Default', '', 'None', 'Title'],
            'Seed' :[123345, 'Default', '', 'int', 'Seed'],
            'FileType' : ['CSV', 'Default', '', 'Upper', 'InputFiles/TrajectoryFile/FileType'],
            'TrajectoryFileName' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/FileName'],
            'TypeColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/Type'],
            'XColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/X'],
            'YColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/Y'],
            'TimeColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/Time'],
            'IDColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/ID'],
            'SpdColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/Speed'],
            'PDMMarketPenetration' : [None, 'Default', '', 'int', 'EquippedVehicles/PDMMarketPenetration'],
            'PDMVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMVehicleIDs'],
            'PDMVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMVehicleTypes'],
            'BSMMarketPenetration' : [None, 'Default', '', 'int', 'EquippedVehicles/BSMMarketPenetration'],
            'BSMVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/BSMVehicleIDs'],
            'BSMVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/BSMVehicleTypes'],
            'RSELocationFile' : [None, 'Default', '', 'None', 'InputFiles/RSELocationFile'],
            'StrategyFile' : ['TCA_Strategy.csv', 'Default', '', 'None', 'InputFiles/StrategyFile'],
            'PDMAllFile' : ['PDM_All.csv', 'Default', '', 'None', 'OutputFiles/PDMAllFile'],
            'PDMTransFile' : ['PDM_Trans.csv', 'Default', '', 'None', 'OutputFiles/PDMTransFile'],
            'BSMTransFile' : ['BSM_Trans.csv', 'Default', '', 'None', 'OutputFiles/BSMTransFile'],
            'BSMExtendedFile' : ['BSM_Trans_More.csv', 'Default', '', 'None', 'OutputFiles/BSMExtendedFile'],
            'BSMExtendedFlag' : [0, 'Default', '', 'None', 'OutputFiles/BSMExtendedFlag'],
            'ColorDisplayDuration' : [2, 'Default', '', 'int', 'ColorDisplayDuration'],
        }

        self.strategy_values = {
            'Title' : ['', 'Default', '', 'None', 'Title'],
            'TimeBetweenPSNSwitches' : [120, 'Default', '', 'int', 'Inputs/DSRC/PSNStrategy/TimeBetweenPSNSwitches' ],
            'DistanceBetweenPSNSwitches' : [3281, 'Default', '', 'int', 'Inputs/DSRC/PSNStrategy/DistanceBetweenPSNSwitches'],
            'RSEFlag' : [0, 'Default', '', 'int', 'Inputs/DSRC/PSNStrategy/RSEFlag'],
            'Gap' : [0, 'Default', '', 'int', 'Inputs/DSRC/PSNStrategy/Gap'],

            'StopStartStrategy' : [1, 'Default', '', 'int', 'Inputs/DSRC/StopStartStrategy/strategy_values'],
            'StopThreshold' : [5, 'Default', '', 'int', 'Inputs/DSRC/StopStartStrategy/StopThreshold'],
            'StopLag' : [15, 'Default', '', 'int', 'Inputs/DSRC/StopStartStrategy/StopLag'],
            'StartThreshold' : [10, 'Default', '', 'int', 'Inputs/DSRC/StopStartStrategy/StartThreshold'],
            'MultipleStops' : [0, 'Default', '', 'int', 'Inputs/DSRC/StopStartStrategy/MultipleStops'],

            'PeriodicStrategy' : [1, 'Default', '', 'int', 'Inputs/DSRC/PeriodicStrategy/strategy_values'],
            'LowSpeedThreshold' : [20, 'Default', '', 'int', 'Inputs/DSRC/PeriodicStrategy/LowSpeedThreshold'],
            'ShortSpeedInterval' : [6, 'Default', '', 'int', 'Inputs/DSRC/PeriodicStrategy/ShortSpeedInterval'],
            'HighSpeedThreshold' : [60, 'Default', '', 'int', 'Inputs/DSRC/PeriodicStrategy/HighSpeedThreshold'],
            'LongSpeedInterval' : [20, 'Default', '', 'int', 'Inputs/DSRC/PeriodicStrategy/LongSpeedInterval'],
            'MaxDeltaSpeed' : [0.10, 'Default', '', 'float', 'Inputs/DSRC/PeriodicStrategy/MaxDeltaSpeed'],

            'TotalCapacity' : [30, 'Default', '', 'int', 'Inputs/DSRC/BufferStrategy/TotalCapacity'],
            'SSRetention' : [4, 'Default', '', 'int', 'Inputs/DSRC/BufferStrategy/SSRetention'],

            'MinRSERange': [492, 'Default', '', 'int', 'Inputs/DSRC/RSEInformation/MinRSERange'],
            'MaxRSERange': [492, 'Default', '', 'int', 'Inputs/DSRC/RSEInformation/MaxRSERange'],
            'TimeoutRSE': [200, 'Default', '', 'int', 'Inputs/DSRC/RSEInformation/TimeoutRSE'],
            'MinNumberofSStoTransmit': [1, 'Default', '', 'int', 'Inputs/DSRC/RSEInformation/MinNumberofSStoTransmit'],
            'RSEReports': [1, 'Default', '', 'int', 'Inputs/DSRC/RSEInformation/RSEReports'],

            'GapMinTime': [3, 'Default', '', 'int', 'Inputs/DSRC/GapInformation/MinTime'],
            'GapMaxTime': [13, 'Default', '', 'int', 'Inputs/DSRC/GapInformation/MaxTime'],
            'GapMinDistance': [164, 'Default', '', 'int', 'Inputs/DSRC/GapInformation/MinDistance'],
            'GapMaxDistance': [820, 'Default', '', 'int', 'Inputs/DSRC/GapInformation/MaxDistance'],

            'PDMCellularFlag': [0, 'Default', '', 'int', 'Inputs/Cellular/PDMCellularFlag'],
            'BSMCellularFlag': [0, 'Default', '', 'int', 'Inputs/Cellular/BSMCellularFlag'],
            'MinNumberofSStoTransmitViaCellular': [1, 'Default', '', 'int', 'Inputs/Cellular/MinNumberofSStoTransmitViaCellular'],
            'DefaultLossPercent': [3, 'Default', '', 'int', 'Inputs/Cellular/DefaultLossPercent'],
            'DefaultLatency': [3000, 'Default', '', 'int', 'Inputs/Cellular/DefaultLatency'],

            'Regions': [{}, 'Default', '', 'region_list', 'Inputs/Cellular/Regions'],
        }

        self.Control = {}
        self.Strategy = {}


    def Error_count(self):
        count = 0
        for key in self.control_values:
            if self.control_values[key][2] != '':
                count +=1
        for key in self.strategy_values:
            if self.strategy_values[key][2] != '':
                count +=1
        return count


    def map_dictionary(self):
        for key in self.control_values:
            self.Control[key] = self.control_values[key][0]

        for key in self.strategy_values:
            self.Strategy[key] = self.strategy_values[key][0]

    def Load_files(self):
        self.Load_Control()
        self.Load_Strategy()
        self.Create_input_summary_file()
        if self.Error_count() >0:
            print 'There is an error in the input values.  Please check TCA_Input_Summary.csv for more information'
            sys.exit(0)
        self.map_dictionary()

    def int_check(self, value, key):
        try:
            int(value)
            return int(value), ''
        except:
            return None, 'Error: %s value must be a integer' % (key)


    def float_check(self, value, key):
        try:
            float(value)
            return float(value), ''
        except:
            return None, 'Error: %s value must be a integer' % (key)


    def Load_Control(self):

        #Load control_values File
        try:
            tree = ET.parse(self.control_file)
            root = tree.getroot()
        except:
            if self.control_file != 'not a file.xml':
                print "Error: cannot find or invalid format for control_values file %s" % self.control_file
                print
            raise

        for key, value in self.control_values.iteritems():

            if root.find(value[4]) != None:

                if value[3] == 'int':
                        A, B = self.int_check(root.find(value[4]).text, key)
                        self.control_values[key][0], self.control_values[key][2] = A, B
                        #TODO Find out way the line below will not work
                        #self.control_values[key][0], self.control_values[key][2] == self.int_check(root.find(value[4]).text, key)
                elif value[3] == 'List_int':
                    self.control_values[key][0] = str(root.find(value[4]).text).split(',')
                    try:
                        self.control_values[key][0] =  [ int(i) for i in self.control_values[key][0]]
                    except:
                        pass
                elif value[3] == 'Upper':
                    self.control_values[key][0] = root.find(value[4]).text.upper()
                else:
                    self.control_values[key][0] = root.find(value[4]).text

                self.control_values[key][1] = 'User_Defined'


        if self.control_values["OutputLevel"][0] !=0:
            if self.control_file == "TCAinput.xml":
                print "Using default file name: TCAinput.xml"
            print "TCA Version 2.0 Beta by Noblis: July 2013"
            print "Start time %s" % (time.strftime('%X', time.localtime(time.time())))
            print "Loading control_values file %s" % (self.control_file)


        #Addtional Error checking
        if self.control_values["OutputLevel"][0] not in [0,1,2,3]:
            self.control_values["OutputLevel"][2] = 'Error: OutputLevel can only be values 0,1,2,3'

        if (self.control_values["PDMMarketPenetration"][0] < 0 or self.control_values["PDMMarketPenetration"][0] > 100) \
            and (self.control_values["PDMMarketPenetration"][0] != None):
           self.control_values["PDMMarketPenetration"][2] = 'Error: PDMMarketPenetration is less than 0 or greater than 100'

        if (self.control_values["BSMMarketPenetration"][0] < 0 or self.control_values["BSMMarketPenetration"][0] > 100) \
            and (self.control_values["BSMMarketPenetration"][0] != None):
           self.control_values["BSMMarketPenetration"][2] = 'Error: BSMMarketPenetration is less than 0 or greater than 100'

        #print (self.TCA_version == 'standalone') , (self.control_values["FileType"][0] == 'CSV') , \
        #    ((self.control_values["XColumn"][0] == None) , (self.control_values["YColumn"][0] == None) , \
        #   (self.control_values["SpdColumn"][0] == None) , (self.control_values["IDColumn"][0] == None) , \
        #   (self.control_values["TimeColumn"][0] == None))
        #
        #print (self.TCA_version == 'standalone') , (self.control_values["FileType"][0] == 'CSV') , \
        #    ((self.control_values["XColumn"][0] == None) or (self.control_values["YColumn"][0] == None) or \
        #   (self.control_values["SpdColumn"][0] == None) or (self.control_values["IDColumn"][0] == None) or \
        #   (self.control_values["TimeColumn"][0] == None))



        if (self.TCA_version == 'standalone') and (self.control_values["FileType"][0] == 'CSV') and \
            ((self.control_values["XColumn"][0] == None) or (self.control_values["YColumn"][0] == None) or \
           (self.control_values["SpdColumn"][0] == None) or (self.control_values["IDColumn"][0] == None) or \
           (self.control_values["TimeColumn"][0] == None)):
                self.control_values["XColumn"][2] = 'Error: Missing either XColumn YColumn SpdColumn IDColumn or TimeColumn xml tag'
                self.control_values["YColumn"][2] = 'Error: Missing either XColumn YColumn SpdColumn IDColumn or TimeColumn xml tag'
                self.control_values["SpdColumn"][2] = 'Error: Missing either XColumn YColumn SpdColumn IDColumn or TimeColumn xml tag'
                self.control_values["IDColumn"][2] = 'Error: Missing either XColumn YColumn SpdColumn IDColumn or TimeColumn xml tag'
                self.control_values["TimeColumn"][2] = 'Error: Missing either XColumn YColumn SpdColumn IDColumn or TimeColumn xml tag'

        if (self.TCA_version == 'standalone') and (self.control_values["PDMMarketPenetration"][0] == None) and \
           (self.control_values["PDMVehicleIDs"][0] == None) and (self.control_values["PDMVehicleTypes"][0] == None) and \
           (self.control_values["BSMVehicleIDs"][0] == None) and (self.control_values["BSMVehicleTypes"][0] == None) and \
           (self.control_values["BSMMarketPenetration"][0] == None):

            self.control_values["PDMMarketPenetration"][2] = 'Error: Must select either include PDMMarketPenetration, PDMVehicleIDs, ' \
                                                    'or PDMVehicleTypes to define equipped vehicles'
            self.control_values["PDMVehicleIDs"][2] = 'Error: Must select either include PDMMarket_Penetration, PDMVehicleIDs, or ' \
                                             'PDMVehicleTypes to define equipped vehicles'
            self.control_values["PDMVehicleTypes"][2] = 'Error: Must select either include PDMMarketPenetration, PDMVehicleIDs, or ' \
                                               'PDMVehicleTypes to define equipped vehicles'


    def Load_Strategy(self):

        if self.control_values['OutputLevel'][0] >= 1:
            print "Loading strategy_values File %s" % (self.control_values["StrategyFile"][0])

        try:
            tree = ET.parse(self.control_values["StrategyFile"][0])
            root = tree.getroot()
        except:
            if self.control_file != 'not a file.xml':
                print "Error: cannot find or invalid format for strategy_values file %s" % self.control_values["StrategyFile"][0]
                print
            raise


        for key, value in self.strategy_values.iteritems():

            if root.find(value[4]) != None:

                if value[3] == 'int':
                        A, B = self.int_check(root.find(value[4]).text, key)
                        self.strategy_values[key][0], self.strategy_values[key][2] = A, B
                        #TODO Find out way the line below will not work
                        #self.control_values[key][0], self.control_values[key][2] == self.int_check(root.find(value[4]).text, key)
                elif value[3] == 'region_list':
                  keys = ['X1','Y1','X2','Y2','LossPercent','Latency','Name']
                  region_list = []
                  for i in range(1,8):
                    region = 'Region' + str(i)
                    if root.find('Inputs/Cellular/Regions/%s' % region) != None: #Region is not defined
                      try:
                        values = map(int, (root.find('Inputs/Cellular/Regions/%s/Point1' % region).text).split(','))
                        values.extend(map(int, (root.find('Inputs/Cellular/Regions/%s/Point2' % region).text).split(',')))
                        values.append(int(root.find('Inputs/Cellular/Regions/%s/LossPercent' % region).text))
                        values.append((float(root.find('Inputs/Cellular/Regions/%s/Latency' % region).text)) / 1000)
                        values.append(root.find('Inputs/Cellular/Regions/%s/Name' % region).text)
                        region_list.append(dict(zip(keys,values)))
                      except:
                        self.strategy_values[key][2] = "Error: Check Cellular values for region %s make sure Point and " \
                                               "LossPercent values are integers and Latency are real values "  % (region)
                  self.strategy_values[key][0] = region_list

                elif value[3] == 'float':
                        A, B = self.float_check(root.find(value[4]).text, key)
                        self.strategy_values[key][0], self.strategy_values[key][2] = A, B
                else:
                    self.strategy_values[key][0] = root.find(value[4]).text

                self.strategy_values[key][1] = 'User_Defined'

    def Create_input_summary_file(self, file_name='TCA_Input_Summary.csv'):
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
                                <EquippedVehicles>
				                    <PDMMarketPenetration>90</PDMMarketPenetration>
			                    </EquippedVehicles>
                            </TrajectoryFile>
                            <RSELocationFile>RSE_locations.csv</RSELocationFile>
                            <StrategyFile>strategy_values.xml</StrategyFile>
                        </InputFiles>
                        <EquippedVehicles>
                            <PDMMarketPenetration>90</PDMMarketPenetration>
                        </EquippedVehicles>
                        <OutputFiles>
                            <PDMTransFile>TCAout.csv</PDMTransFile>
                            <PDMAllFile>TCAoutALL.csv</PDMAllFile>
                            <BSMTransFile>TCAoutBSM.csv</BSMTransFile>
                        </OutputFiles>
                        <IDS>All</IDS>
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
                                <FileName>VISSIM.fzp</FileName>
                            </TrajectoryFile>
                            <RSELocationFile>RSE_locations.csv</RSELocationFile>
                            <StrategyFile>strategy_values.xml</StrategyFile>
                        </InputFiles>
                        <EquippedVehicles>
                            <PDMVehicleTypes>1,2</PDMVehicleTypes>
                            <PDMMarketPenetration>90</PDMMarketPenetration>
                        </EquippedVehicles>
                        <OutputFiles>
                            <TransmittedSnapShotsFile>TCAout.csv</TransmittedSnapShotsFile>
                            <AllSnapShotsFile>TCAoutALL.csv</AllSnapShotsFile>
                            <TransmittedBSMFile>TCAoutBSM.csv</TransmittedBSMFile>
                        </OutputFiles>
                        <IDS>All</IDS>
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
                        <IDS>All</IDS>
                    </ControlFile>""")




        with open('tca_delete_me_test_file_bad2.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8"?>
                    <ControlFile>
                    <OutputLevel>0</OutputLevel>
                    </ControlFile>""")

    def test_load_good(self):
        CF = ControlFiles('tca_delete_me_test_file_good.xml')
        CF.Load_Control()
        assert CF.Error_count() == 0
        assert CF.control_values["PDMMarketPenetration"][0] == 90
        assert CF.control_values["RSELocationFile"][0] == 'RSE_locations.csv'
        assert CF.control_values["YColumn"][0] == 'y_val'

    def test_load_good_vissim(self):
        CF = ControlFiles('tca_delete_me_test_file_good_vissim.xml')
        CF.Load_Control()
        assert CF.Error_count() == 0
        assert CF.control_values["FileType"][0] == 'VISSIM'
        assert CF.control_values["TrajectoryFileName"][0] == 'VISSIM.fzp'
        assert CF.control_values["PDMVehicleTypes"][0] == [1,2]


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
        try:
            CF = ControlFiles('not a file.xml')
            CF.Load_Control()
            assert False
        except:
            assert True


    def tearDown(self):
        os.remove('tca_delete_me_test_file_bad2.xml')
        os.remove('tca_delete_me_test_file_bad.xml')
        os.remove('tca_delete_me_test_file_good_vissim.xml')
        os.remove('tca_delete_me_test_file_good.xml')


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
                        </EquippedVehicles>
                    </TrajectoryFile>
                    <StrategyFile>Strategy_cellular.xml</StrategyFile>
                </InputFiles>
                </ControlFile>
            """)

        with open('tca_delete_me_test_file_good.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
                    <strategy_values>
                      <Title>J2735 Noblis Modified strategy_values</Title>
                    <Inputs>
                     <DSRC>
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
                     <RSEInformation>
                      <MinRSERange>492</MinRSERange>
                      <MaxRSERange>492</MaxRSERange>
                      <TimeoutRSE>200</TimeoutRSE>
                      <MinNumberofSStoTransmit>1</MinNumberofSStoTransmit>
                      <RSEReports>1</RSEReports>
                      </RSEInformation>
                     <GapInformation>
                      <MinTime>3</MinTime>
                      <MaxTime>13</MaxTime>
                      <MinDistance>164</MinDistance>
                      <MaxDistance>820</MaxDistance>
                      </GapInformation>
                      </DSRC>
                     <Cellular>
                      <CellularFlag>0</CellularFlag>
                      <MinNumberofSStoTransmitViaCellular>3</MinNumberofSStoTransmitViaCellular>
                      <DefaultLossPercent>3</DefaultLossPercent>
                      <DefaultLatency>1000</DefaultLatency>
                      </Cellular>
                      </Inputs>
                      </strategy_values>""")

        with open('tca_delete_me_test_file_bad.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
                        <strategy_values>
                          <Title>J2735 Noblis Modified strategy_values</Title>
                        <Inputs>
                        <DSRC>
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
                         <RSEInformation>
                          <MinRSERange>492.0</MinRSERange>
                          <MaxRSERange>492</MaxRSERange>
                          <TimeoutRSE>200</TimeoutRSE>
                          <MinNumberofSStoTransmit>1</MinNumberofSStoTransmit>
                          <RSEReports>1</RSEReports>
                          </RSEInformation>
                         <GapInformation>
                          <MinTime>3</MinTime>
                          <MaxTime>13</MaxTime>
                          <MinDistance>164</MinDistance>
                          <MaxDistance>820</MaxDistance>
                          </GapInformation>
                          </DSRC>
                         <Cellular>
                          <CellularFlag>0</CellularFlag>
                          <MinNumberofSStoTransmitViaCellular>3</MinNumberofSStoTransmitViaCellular>
                          <DefaultLossPercent>3</DefaultLossPercent>
                          <DefaultLatency>1000</DefaultLatency>
                          </Cellular>
                          </Inputs>
                          </strategy_values>""")

        with open('tca_delete_me_celluar_test_file_bad.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
        <Strategy>
          <Title>J2735 Noblis Modified Strategy</Title>
          <Inputs>
            <DSRC>
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
        <RSEInformation>
         <!--  Min range for communication to RSE in feet  -->
         <MinRSERange>492</MinRSERange>
         <!--  Max range for communication to RSE in feet  -->
         <MaxRSERange>492</MaxRSERange>
         <!--  Timeout gap in seconds for RSE interaction  -->
         <TimeoutRSE>200</TimeoutRSE>
         <!--  Number of SS transmitted at a time.    -->
         <MinNumberofSStoTransmit>1</MinNumberofSStoTransmit>
         <!--  Number of times vehicle can transmit to RSE (0 value all of the time)  -->
         <RSEReports>1</RSEReports>
        </RSEInformation>
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
        </DSRC>
        <Cellular>
              <!-- If cellular communication is used:
                0: Not used
                1: Cellular comm used (Vehicles transmit snapshots via cellular according to defined latency) -->
                <PDMCellularFlag>1</PDMCellularFlag>
                <BSMCellularFlag>0</BSMCellularFlag>
                <MinNumberofSStoTransmitViaCellular>1</MinNumberofSStoTransmitViaCellular>
                <DefaultLossPercent>10</DefaultLossPercent>
                <DefaultLatency>1000</DefaultLatency>
                <Regions>
                  <Region1>
                    <Name>Cellular_Region1</Name>
                    <Point1>-6153,-2543</Point1>
                    <Point2>-5977,-2637</Point2>
                    <LossPercent>2</LossPercent>
                    <Latency>2000</Latency>
                  </Region1>
                  <Region2>
                    <Name>Cellular_Region2</Name>
                    <Point1>-5923,-2545</Point1>
                    <Point2>-5761,-2625</Point2>
                    <LossPercent>1</LossPercent>
                    <Latency>500</Latency>
                  </Region2>
                  <Region3>
                    <Name>Cellular_Region3</Name>
                    <Point1>-5689,-2525</Point1>
                    <Point2>-5400,-2659</Point2>
                    <LossPercent>50</LossPercent>
                    <Latency>8000</Latency>
                  </Region3>
                  <Region4>
                    <Name>Cellular_Region4</Name>
                    <Point1>-5380,-2539</Point1>
                    <Point2>-4918,-2640</Point2>
                    <LossPercent>4</LossPercent>
                    <Latency>200</Latency>
                  </Region4>
                  <Region5>
                    <Name>Cellular_Region5</Name>
                    <Point1>-5626,-1932</Point1>
                    <Point2>-5460,-2112</Point2>
                    <LossPercent>50</LossPercent>
                    <Latency>5000</Latency>
                  </Region5>
                  <Region6>
                    <Name>Cellular_Region6</Name>
                    <Point1>-5635,-2172</Point1>
                    <Point2>-5470,-2320</Point2>
                    <LossPercent>1</LossPercent>
                    <Latency>1000</Latency>
                  </Region6>
                  <Region7>
                    <Name>Cellular_Region7</Name>
                    <Point1>-5645,-2761</Point1>
                    <Point2>-5442,-3170</Point2>
                    <LossPercent>2</LossPercent>
                    <Latency>1000</Latency>
                  </Region7>
                </Regions>
              </Cellular>
            </Inputs>
          </Strategy>""")

    def test_load_strategy(self):
        CF = ControlFiles('test_control_delete_me.xml')
        CF.Load_Control()
        assert  CF.Error_count() == 0
        CF.control_values['StrategyFile'][0] = 'tca_delete_me_test_file_good.xml'
        CF.Load_Strategy()

        assert CF.Error_count() == 0
        assert CF.strategy_values["StopThreshold"][0] == 5
        assert CF.strategy_values["StartThreshold"][0] == 10
        assert CF.strategy_values["GapMinDistance"][0] == 164

    def test_load_bad_strategy(self):
        CF = ControlFiles('test_control_delete_me.xml')
        CF.Load_Control()
        assert  CF.Error_count() == 0
        CF.control_values['StrategyFile'][0] = 'tca_delete_me_test_file_bad.xml'
        CF.Load_Strategy()
        assert  CF.Error_count() == 2
        assert CF.strategy_values["ShortSpeedInterval"][2] != ''
        assert CF.strategy_values["MinRSERange"][2] != ''


    def test_cellular_regions(self):
        CF = ControlFiles('test_control_delete_me.xml')
        CF.Load_Control()
        assert  CF.Error_count() == 0
        CF.control_values['StrategyFile'][0] = 'tca_delete_me_celluar_test_file_bad.xml'
        CF.Load_Strategy()
        print CF.strategy_values['Regions']
        assert CF.strategy_values['Regions'][0][0]['LossPercent'] == 2
        assert CF.strategy_values['Regions'][0][3]['Latency'] == 0.2


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
        CF.control_values['StrategyFile'][0] = 'tca_delete_me_test_file_bad.xml'
        CF.Load_Strategy()
        assert CF.Error_count() == 2
        CF.Create_input_summary_file()

    def tearDown(self):
        import os
        os.remove('test_control_delete_me.xml')
        os.remove('tca_delete_me_test_file_good.xml')
        os.remove('tca_delete_me_test_file_bad.xml')
        os.remove('tca_delete_me_celluar_test_file_bad.xml')


if __name__ == '__main__':
    unittest.main()