#standard
import math
import sys
import unittest
import time
import logging
import os
from xml.dom import minidom
import xml.etree.ElementTree as ET

#get current directory of file
curdir = os.path.dirname(os.path.realpath(__file__)) + os.sep
control_values =  {
            'OutputLevel' : [0, 'Default', '', 'int', 'OutputLevel'],
            'Title' : ['', 'Default', '', 'None', 'Title'],
            'Seed' :[123345, 'Default', '', 'int', 'Seed'],
            'FileType' : ['CSV', 'Default', '', 'Upper', 'InputFiles/TrajectoryFile/FileType'],
            'TrajectoryFileName' : [None, 'Default', '', 'file', 'InputFiles/TrajectoryFile/FileName'],
            'TypeColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/Type'],
            'XColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/X'],
            'YColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/Y'],
            'TimeColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/Time'],
            'IDColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/ID'],
            'SpdColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/Speed'],
            'AccelColumn' : [None, 'Default', '', 'None', 'InputFiles/TrajectoryFile/CSVTrajectoryFileFields/Accel'],

            'PDMMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/PDMMarketPenetration'],
            'PDMVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMVehicleIDs'],
            'PDMVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMVehicleTypes'],

            'BSMMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/BSMMarketPenetration'],
            'BSMVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/BSMVehicleIDs'],
            'BSMVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/BSMVehicleTypes'],

            'DualPDMBSMMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/DualPDMBSMMarketPenetration'],
            'DualPDMBSMVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/DualPDMBSMVehicleIDs'],
            'DualPDMBSMVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/DualPDMBSMVehicleTypes'],

            'CAMMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/CAMMarketPenetration'],
            'CAMVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/CAMVehicleIDs'],
            'CAMVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/CAMVehicleTypes'],
            'SPOTMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/SPOTMarketPenetration'],
            'SPOTVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/SPOTVehicleIDs'],
            'SPOTVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/SPOTVehicleTypes'],

            'PDMDSRCMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/PDMEquipped/DSRC/MarketPenetration'],
            'PDMDSRCVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMEquipped/DSRC/VehicleTypes'],
            'PDMDSRCVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMEquipped/DSRC/VehicleIDs'],
            'PDMCellularMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/PDMEquipped/Cellular/MarketPenetration'],
            'PDMCellularVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMEquipped/Cellular/VehicleTypes'],
            'PDMCellularVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMEquipped/Cellular/VehicleIDs'],
            'PDMDualCommMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/PDMEquipped/DualComm/MarketPenetration'],
            'PDMDualCommVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMEquipped/DualComm/VehicleTypes'],
            'PDMDualCommVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMEquipped/DualComm/VehicleIDs'],
            'BSMDSRCMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/BSMEquipped/DSRC/MarketPenetration'],
            'BSMDSRCVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/BSMEquipped/DSRC/VehicleTypes'],
            'BSMDSRCVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/BSMEquipped/DSRC/VehicleIDs'],
            'BSMCellularMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/BSMEquipped/Cellular/MarketPenetration'],
            'BSMCellularVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/BSMEquipped/Cellular/VehicleTypes'],
            'BSMCellularVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/BSMEquipped/Cellular/VehicleIDs'],
            'BSMDualCommMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/BSMEquipped/DualComm/MarketPenetration'],
            'BSMDualCommVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/BSMEquipped/DualComm/VehicleTypes'],
            'BSMDualCommVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/BSMEquipped/DualComm/VehicleIDs'],
            'PDMBSMDSRCMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/PDMBSMEquipped/DSRC/MarketPenetration'],
            'PDMBSMDSRCVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMBSMEquipped/DSRC/VehicleTypes'],
            'PDMBSMDSRCVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMBSMEquipped/DSRC/VehicleIDs'],
            'PDMBSMCellularMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/PDMBSMEquipped/Cellular/MarketPenetration'],
            'PDMBSMCellularVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMBSMEquipped/Cellular/VehicleTypes'],
            'PDMBSMCellularVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMBSMEquipped/Cellular/VehicleIDs'],
            'PDMBSMDualCommMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/PDMBSMEquipped/DualComm/MarketPenetration'],
            'PDMBSMDualCommVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMBSMEquipped/DualComm/VehicleTypes'],
            'PDMBSMDualCommVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/PDMBSMEquipped/DualComm/VehicleIDs'],

            'CAMDSRCMarketPenetration' : [0, 'Default', '', 'int', 'EquippedVehicles/CAMEquipped/DSRC/MarketPenetration'],
            'CAMDSRCVehicleTypes' : [[], 'Default', '', 'List_int', 'EquippedVehicles/CAMEquipped/DSRC/VehicleTypes'],
            'CAMDSRCVehicleIDs' : [[], 'Default', '', 'List_int', 'EquippedVehicles/CAMEquipped/DSRC/VehicleIDs'],

            'RSELocationFile' : [None, 'Default', '', 'file', 'InputFiles/RSELocationFile'],
            'SPOTLocationFile' : [None, 'Default', '', 'file', 'InputFiles/SPOTLocationFile'],
            'StrategyFile' : [None, 'Default', '', 'file', 'InputFiles/StrategyFile'],
            'RegionsFile' : [None, 'Default', '', 'file', 'InputFiles/RegionsFile'],
            'PDMAllFile' : ['PDM_All.csv', 'Default', '', 'file', 'OutputFiles/PDMAllFile'],
            'PDMTransFile' : ['PDM_Trans.csv', 'Default', '', 'file', 'OutputFiles/PDMTransFile'],
            'BSMTransFile' : ['BSM_Trans.csv', 'Default', '', 'file', 'OutputFiles/BSMTransFile'],
            'CAMTransFile' : ['CAM_Trans.csv', 'Default', '', 'file', 'OutputFiles/CAMTransFile'],
            'SPOTTravelFile' : ['SPOT_TravelRecords.csv', 'Default', '', 'file', 'OutputFiles/SPOTTravelFile'],
            'SPOTBehaviorFile' : ['SPOT_BehaviorRecords.csv', 'Default', '', 'file', 'OutputFiles/SPOTBehaviorFile'],

            'BSMTransColor' : [[0,0,204], 'Default', '', 'List_int', 'Color/BSMTransColor'], # Default: dark blue
            'PDMPeriodicColor' : [[204,0,204], 'Default', '', 'List_int', 'Color/PDMPeriodicColor'], # Default: light purple
            'PDMStopColor' : [[204,0,0], 'Default', '', 'List_int', 'Color/PDMStopColor'], # Default: red
            'PDMStartColor' : [[102,204,0], 'Default', '', 'List_int', 'Color/PDMStartColor'], # Default: green
            'PDMDSRCTransColor' : [[0,0,0], 'Default', '', 'List_int', 'Color/PDMDSRCTransColor'], # Default: black
            'PDMCellularTransColor' : [[0,204,204], 'Default', '', 'List_int', 'Color/PDMCellularTransColor'], # Default: light blue
            'SpotBehaviorColor' : [[102,0,204], 'Default', '', 'List_int', 'Color/SpotBehaviorColor'], # Default: dark purple
            'SpotTravelColor' : [[0,102,204], 'Default', '', 'List_int', 'Color/SpotTravelColor'], # Default: blue
            'SpotTransColor' : [[255,255,71], 'Default', '', 'List_int', 'Color/SpotTransColor'], # Default: yellow
            'CAMTransColor' : [[204,102,0], 'Default', '', 'List_int', 'Color/CAMTransColor'], # Default: orange
            'DualPDMBSMColor' : [[255,255,255], 'Default', '', 'List_int', 'Color/DualPDMBSMColor'], # Default: white
            'PDMDefaultColor' : [[255,255,255], 'Default', '', 'List_int', 'Color/PDMDefaultColor'], # Default: white
            'BSMDefaultColor' : [[255,255,255], 'Default', '', 'List_int', 'Color/BSMDefaultColor'], # Default: white
            'DefaultColor' : [[255,255,255], 'Default', '', 'List_int', 'Color/DefaultColor'], # Default: white
            'ColorDisplay' : [False, 'Default', '', 'Boolean', 'Color/ColorDisplay'],
            'ColorDisplayDuration' : [1, 'Default', '', 'int', 'Color/ColorDisplayDuration'],
        }

strategy_values = {
            'Title' : ['', 'Default', '', 'None', 'Title'],
            'TimeBeforePDMCollection' : [120, 'Default', '', 'int', 'Inputs/PDM/TimeBeforePDMCollection' ],
            'DistanceBeforePDMCollection' : [1680, 'Default', '', 'int', 'Inputs/PDM/DistanceBeforePDMCollection' ],
            'GapMinTime': [3, 'Default', '', 'int', 'Inputs/PDM/PSNStrategy/GapInformation/MinTime'],
            'GapMaxTime': [13, 'Default', '', 'int', 'Inputs/PDM/PSNStrategy/GapInformation/MaxTime'],
            'GapMinDistance': [164, 'Default', '', 'int', 'Inputs/PDM/PSNStrategy/GapInformation/MinDistance'],
            'GapMaxDistance': [820, 'Default', '', 'int', 'Inputs/PDM/PSNStrategy/GapInformation/MaxDistance'],

            'TimeBetweenPSNSwitches' : [120, 'Default', '', 'int', 'Inputs/PDM/PSNStrategy/TimeBetweenPSNSwitches' ],
            'DistanceBetweenPSNSwitches' : [3281, 'Default', '', 'int', 'Inputs/PDM/PSNStrategy/DistanceBetweenPSNSwitches'],
            'Gap' : [0, 'Default', '', 'int', 'Inputs/PDM/PSNStrategy/Gap'],

            'StopStartStrategy' : [1, 'Default', '', 'int', 'Inputs/PDM/StopStartStrategy/StrategyID'],
            'StopThreshold' : [5, 'Default', '', 'int', 'Inputs/PDM/StopStartStrategy/StopThreshold'],
            'StopLag' : [15, 'Default', '', 'int', 'Inputs/PDM/StopStartStrategy/StopLag'],
            'StartThreshold' : [10, 'Default', '', 'int', 'Inputs/PDM/StopStartStrategy/StartThreshold'],
            'MultipleStops' : [0, 'Default', '', 'int', 'Inputs/PDM/StopStartStrategy/MultipleStops'],

            'PeriodicStrategy' : [1, 'Default', '', 'int', 'Inputs/PDM/PeriodicStrategy/StrategyID'],
            'LowSpeedThreshold' : [20, 'Default', '', 'int', 'Inputs/PDM/PeriodicStrategy/LowSpeedThreshold'],
            'ShortSpeedInterval' : [4, 'Default', '', 'int', 'Inputs/PDM/PeriodicStrategy/ShortSpeedInterval'],
            'HighSpeedThreshold' : [60, 'Default', '', 'int', 'Inputs/PDM/PeriodicStrategy/HighSpeedThreshold'],
            'LongSpeedInterval' : [20, 'Default', '', 'int', 'Inputs/PDM/PeriodicStrategy/LongSpeedInterval'],
            'MaxDeltaSpeed' : [0.10, 'Default', '', 'float', 'Inputs/PDM/PeriodicStrategy/MaxDeltaSpeed'],

            'TotalCapacity' : [30, 'Default', '', 'int', 'Inputs/PDM/BufferStrategy/TotalCapacity'],
            'SSRetention' : [4, 'Default', '', 'int', 'Inputs/PDM/BufferStrategy/SSRetention'],

            'MinRSERange': [492, 'Default', '', 'int', 'Inputs/DSRC/RSEInformation/MinRSERange'],
            'MaxRSERange': [492, 'Default', '', 'int', 'Inputs/DSRC/RSEInformation/MaxRSERange'],
            'TimeoutRSE': [200, 'Default', '', 'int', 'Inputs/DSRC/RSEInformation/TimeoutRSE'],
            'MinNumberofPDMtoTransmitViaDSRC' : [4, 'Default', '', 'int', 'Inputs/DSRC/RSEInformation/MinNumberofPDMtoTransmitViaDSRC'],

            'SPOTdeviceRange' : [32.8, 'Default', '', 'float', 'Inputs/SPOT/DeviceRange'], #SPOT devices usually cover 20 meters (10 meter radius or 32.8 feet) of roadway
            'SPOTBehaviorSensingFrequency' : [0.3, 'Default', '', 'float', 'Inputs/SPOT/BehaviorSensingFrequency'],
            'SPOTaccelThreshold' : [-0.25, 'Default', '', 'float', 'Inputs/SPOT/AccelThreshold'],
            'SPOTyawrateThreshold' : [9.8, 'Default', '', 'float', 'Inputs/SPOT/YawrateThreshold'],

            'BrakeThreshold': [-0.2, 'Default', '', 'float', 'Inputs/BSM/BrakeThreshold'],

            'PDMFrequencyDSRC': [0.0, 'Default', '', 'float', 'Inputs/PDM/DSRCFrequency'],
            'PDMFrequencyCellular': [0.0, 'Default', '', 'float', 'Inputs/PDM/CellularFrequency'],
            'BSMFrequencyCellular': [0.0, 'Default', '', 'float', 'Inputs/BSM/CellularFrequency'],
            'BSMFrequencyDSRC': [0.0, 'Default', '', 'float', 'Inputs/BSM/DSRCFrequency'],
        }


def write_default(filename, filetype, parameters):
    root = ET.Element(filetype)
    for tag, value in parameters.iteritems():
        children = value[4].split('/')
        length = len(children)-1
        found_path = False
        path = value[4].rsplit('/',1)[0]
        while length > 0 and found_path == False:
              if root.findall("." + path):
                    found_path = True
              else:
                    path = path.rsplit('/',1)[0]
                    length -=1
        if length > 0:
            subelement = root.find(path)
        else:
            subelement = root
        for r in range(length, len(children)-1):
              x = ET.SubElement(subelement, children[r])
              subelement = x
        ET.SubElement(subelement, children[-1]).text = str(value[0])

    root.find('Title').text = "Default" + filetype

    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string).toprettyxml(indent = '    ')

    with open(filename, 'wb') as f_out:
            f_out.write(reparsed)
            

def write_default_regions(filename):
    with open(filename, 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?> 
<Regions> 
    <Cell_Regions>
      <!-- Default snapshot transmission loss percentage for cellular transmissions outside defined cellular regions. -->
      <DefaultLossPercent>2</DefaultLossPercent>
      <!-- Default latency (seconds) for cellular transmissions outside defined cellular regions -->
      <DefaultLatency>1</DefaultLatency> 
      <!-- Default mininum number of PDMs needed in the vehicle buffer for cellular transmission -->   
      <MinPDMtoTransmit>4</MinPDMtoTransmit>
      <Cell_Region> 
          <Title>Cellular_Region1</Title> 
          <!-- Upper left x and y coordinates of the region rectangle -->     
          <UpperLeftPoint>
            <X>-5314</X>
            <Y>-2530</Y>
          </UpperLeftPoint>
          <!-- Lower right x and y coordinates of the region rectangle -->
          <LowerRightPoint>
            <X>-4917</X>
            <Y>-2705</Y>          
          </LowerRightPoint> 
          <!-- Transmission loss percentage of cellular transmissons made within the region -->
          <LossPercent>5</LossPercent>
          <!-- Transmission latency (seconds) of cellular transmissions made within the region -->
          <Latency>2</Latency>
      </Cell_Region>  
    </Cell_Regions>
    <Event_Regions>
        <Region>
          <Title>AirTempHigh</Title>
          <UpperLeftPoint>
            <X>-6157</X>
            <Y>-2530</Y>
          </UpperLeftPoint>
          <LowerRightPoint>
            <X>-5624</X>
            <Y>-2705</Y>          
          </LowerRightPoint> 
          <TimePeriods> 
            <Period> 
                <!-- Start and end time that the event region is active -->    
                <StartTime>0</StartTime> 
                <EndTime>1200</EndTime>
             </Period>
          </TimePeriods> 
          <Events>
              <Event>
                <Title>AirTemp</Title>
                <!-- Standard deviation probability requires a mean and a standard deviation (SD) --> 
                <Mean>7</Mean>
                <SD>4</SD>
                <!-- Static recheck value (seconds) determines how often the TCA checks this event -->
                <Recheck>10</Recheck>
              </Event>          
          </Events>
        </Region>
        <Region>
          <Title>HeavyRain</Title>      
          <UpperLeftPoint>
            <X>-5314</X>
            <Y>-2530</Y>
          </UpperLeftPoint>
          <LowerRightPoint>
            <X>-4917</X>
            <Y>-2705</Y>          
          </LowerRightPoint>  
          <TimePeriods>
              <Period>
                <StartTime>50</StartTime> 
                <EndTime>100</EndTime>
              </Period>
              <Period>
                <StartTime>300</StartTime>
                <EndTime>800</EndTime>
              </Period>
          </TimePeriods> 
          <Events>
              <Event>
                <Title>Wipers</Title>
                <!-- Static probability (%) of occurrence -->
                <Probability>85</Probability>
                <!-- The mean value for generating a random recheck value (seconds) using a Poisson distribution -->
                <RecheckPoisson>7</RecheckPoisson>
              </Event>
              <Event>
                <Title>TractionControl</Title>
                <Probability>5</Probability>
                <Recheck>2</Recheck>
              </Event>
          </Events>      
        </Region>
    </Event_Regions>        
</Regions>"""
)


def set_logger(console_level = logging.INFO, file_level = logging.DEBUG, include_file = True, append_file = False):
    """
    Creates the log file

    :param console_level: level to log items to screen
    :param file_level:  level to log items to file
    :param include_file:  include log file
    :param append_file: append to last file
    :return: logger object
    """

    if not append_file:
        # os.remove(curdir + 'tca2.log')
        try:
            os.remove(curdir + 'tca2.log')
        except:
            pass

    logger = logging.getLogger(curdir + 'tca2')
    logger.setLevel(file_level)

    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(message)s'))
    ch.setLevel(console_level)
    logger.addHandler(ch)

    if include_file:
        fh = logging.FileHandler(curdir + 'tca2.log')
        # fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        fh.setLevel(file_level)
        logger.addHandler(fh)

    return logger


logger = set_logger(include_file = True, file_level = logging.DEBUG)

#-------------------------------------------------------------------------
def SPOT_time(tp, interval):
    """
    Determines if the timeperiod is valid for generating an ITS Spot message

    :param tp: float of current time period
    :param interval: float of the frequency for checking ITS Spot behavior record triggers
    :return: True is the tp is valid, otherwise False
    """

    l = [str(x) for x in range(0, 10, int(str(interval)[-1]))]

    if str(tp)[-1] in l:
        return True

    return False

#-------------------------------------------------------------------------
def Get_Heading_Change(heading_last, heading_current):
    """
    determines the change in heading

    :param heading_last: float of previous handing
    :param heading_current: float of current heading
    :return: float of the difference in heading
    """
    r = heading_current - heading_last + 180
    return (r % 360) - 180



#-------------------------------------------------------------------------
def Chk_Range(x1, y1, x2, y2):

    """
    Determine the range between two points

    :param x1: float value for X for first point
    :param y1: float value for Y for first point
    :param x2: float value for X for 2nd point
    :param y2: float value for Y for 2nd point
    :return: float distance between the two points
    """
    unitValue = 1 #1 = linear distance #2 - Spherical distance

    ran = None

    if unitValue ==1:
        ran = math.sqrt((float(y2) - float(y1)) ** 2 + (float(x2) - float(x1)) ** 2)
    elif unitValue==2:

        rad = 3958.76 #Earth radius in Miles

        #Convert to radians
        p1lat = float(x1) / 180 * math.pi
        p1long = float(y1) / 180 * math.pi
        p2lat = float(x2) / 180 * math.pi
        p2long = float(y2) / 180 * math.pi

        if (p1lat == p2lat) and (p1long == p2long):
            ran = float(0)
        else:
            ran = math.acos(math.sin(p1lat) * math.sin(p2lat) + math.cos(p1lat) * math.cos(p2lat)
                  * math.cos(p2long - p1long)) * rad

    return ran


def file_fzp_start(filename):
    """
    finds the start of the fzp data

    :param filename: string of the fzp file name
    :return: number of lines to skip at top of file
    """

    with open(filename) as in_f:
        c= 0
        cols = []
        #find start of VISSIM data
        line = in_f.readline()
        while 'VehNr;' not in line:
            line = in_f.readline()
            cols = [x.strip() for x in line.split(';')][:-1]
            c +=1

        return {'lines_to_skip' : c, 'header_cols' : cols}



#-------------------------------------------------------------------------
# (x1,y1) : Top left of rectangle, (x2,y2) : Bottom right of rectangle, (x3,y3) : Point in question
def Chk_Cellular_Range(x1, y1, x2, y2, x3, y3):

    """
    determines in point is in a rectangle

    :param x1: float value for X for first point
    :param y1: float value for Y for first point
    :param x2: float value for X for 2nd point
    :param y2: float value for Y for 2nd point
    :param x3: float value for X for 3rd point
    :param y3: float value for Y for 3rd point
    :return: boolean value True if in, False if out
    """
    if((x3>=x1) & (y3<=y1) & (x3<=x2) & (y3>=y2)):
        return True
    else:
        return False

#-------------------------------------------------------------------------
def Get_Heading(x1, y1, x2, y2):
    """
    Returns the Heading based on two points

    :param x1: float value for X for first point
    :param y1: float value for Y for first point
    :param x2: float value for X for 2nd point
    :param y2: float value for Y for 2nd point
    :return: float new heading value
    """

    heading = 0
    dx = x2 - x1
    dy = y2 - y1

    if dx != 0:
      heading = (90 - math.degrees(math.atan2(dy,dx)) + 360) % 360

    elif dy > 0: heading = 0

    elif dy < 0: heading = 180

    return heading

#-------------------------------------------------------------------------
def clear_old_files(CF):

        files = [
            CF.Control["PDMTransFile"],
            CF.Control["PDMAllFile"],
            CF.Control["BSMTransFile"],
            CF.Control["CAMTransFile"],
            CF.Control['SPOTTravelFile'],
            CF.Control['SPOTBehaviorFile']]

        for f in files:
            try:
                os.remove(f)
            except:
                pass


#-------------------------------------------------------------------------
def report_errors(errors):
    """
    prints out any errors found

    :param errors: list of errors
    """
    if len(errors) > 0:
        for error in errors:
            logger.debug(error)
        sys.exit(0)


class Timer:

   def __init__(self, enabled=False):
        """
        Create Timer class

        :param enabled: Boolean if used
        """
        self.timers = {}
        self.last_start = ''
        self.enabled = enabled

   def valid_title(self, title):
       """
       Checks if title of timer item is validate

       :param title: string of title
       :return: boolean True if validate, False if not
       """
       if title in self.timers.keys() and isinstance(title, str) and self.timers[title]['count']>0:
           return True
       else:
           return False

   def __getitem__(self, title):
        """
        prints out summary information for timer

        :param title: title of time name
        :return: string of summary information about that timer
        """
        if self.valid_title(title):
                return title + ', ' + \
                       str(self.stats(title)) + ', ' + \
                       str(self.stats(title, type='max')) + ', ' + \
                       str(self.stats(title, type='avg')) + ', ' + \
                       str(self.stats(title, type='count')) + ', ' + \
                       str(self.stats(title, type='last'))
        else:
            print ('Timer Error %s not created or stopped' % title)



   def current(self, title):
       """
       Returns the current timer title

       :param title: title of timer
       :return: name of current timer or 0
       """
       if self.valid_title(title):
            return self.timers[title]['last']
       else:
            return 0


   def stats(self, title, type='SUM'):
        """
        returns the sum, max, average, count, or last value of a time title.

        :param title: name of timer value
        :param type: type of stats to produce
        :return: stat of the given timer value
        """
        if self.valid_title(title):
                if type.upper() == 'SUM':
                    return self.timers[title]['sum']
                elif type.upper() == 'MAX':
                    return self.timers[title]['max']
                elif type.upper() == 'AVG':
                    return self.timers[title]['sum'] / self.timers[title]['count']
                elif type.upper() == 'COUNT':
                    return self.timers[title]['count']
                elif type.upper() == 'LAST':
                    return  self.timers[title]['last']
        else:
            print('Error timer %s was never stopped' % title)




   def start(self, title):
       """
       starts a given timer

       :param title: string name of the timer
       """
       if self.enabled:
            if title not in self.timers.keys():
                self.timers[title] = {'st' : time.time(),
                                      'sum' : 0.0,
                                      'count' : 0,
                                      'max' : 0.0,
                                      'last' : None,
                                     }
            else:
                self.timers[title]['st'] = time.time()

            self.last_start = title


   def stop(self, title=''):
        """
        stops a given timer title

        :param title: name of the timer
        """
        if self.enabled:
            if title == '':
               title = self.last_start
            if self.timers.has_key(title):
               new_time = time.time() - self.timers[title]['st']
               self.timers[title]['sum'] +=  new_time
               self.timers[title]['count'] += 1
               self.timers[title]['last'] = new_time
               if new_time > self.timers[title]['max']:
                   self.timers[title]['max'] = new_time



   def drop(self,title):
        """
        removes timer from list

        :param title: name of a timer
        """

        if self.enabled:
            del self.timers[title]

   def header(self):
       """
       :return: string of header for timer file
       """
       return 'title,sum,max,avg,len,last\n'

   def write(self):
        """
        writes all timers values to string

        :return: string of the timer list
        """
        if self.enabled and len(self.timers) > 0:
            l = []
            for title in sorted(self.timers):
                if self.valid_title(title):
                    l.append(self.__getitem__(title))
            return '\n'.join(l)
        else:
            return ''




#*************************************************************************
class TestTimer(unittest.TestCase):

    def test_timer(self):
        t1=Timer(enabled = True)

        t1.start('test1')
        time.sleep(2)
        t1.stop()
        assert  ( round(t1.current('test1'), 2) >= 2.0) and (t1.current('test1') < 2.1)

        t1.start('test2')
        time.sleep(3)
        t1.stop('test2')

        assert  (round(t1.current('test2'), 2) >= 3.0) and (t1.current('test2') < 3.1)

        t1.start('test2')
        time.sleep(2)
        t1.stop()
        assert  (round (t1.stats('test2'), 2) >= 5.0) and (t1.stats('test2') < 5.1)

class CoreTests(unittest.TestCase):

    def test_range(self):
        assert 1 == int(Chk_Range(1,1,2,2))
        assert 5.0 == Chk_Range(-2,1,1,5)
        assert 0.0 == Chk_Range(1,1,1,1)

    def test_errors(self):
        e = []
        report_errors(e)

    def test_cellular_range(self):
        assert True == Chk_Cellular_Range(-2,1,0,0,-1,1)
        assert False == Chk_Cellular_Range(-2,1,0,0,1,0)

    def test_heading(self):
        assert 0 == Get_Heading(0,-1,0,0)
        assert 45 == Get_Heading(1,1,3,3)
        assert 90 == Get_Heading(-1,0,0,0)
        assert 180 == Get_Heading(0,0,0,-1)
        assert 225 == Get_Heading(-1,-1,-5,-5)
        assert 270 == Get_Heading(0,0,-1,0)

    def test_SPOT(self):
        assert True == SPOT_time(1.3, 0.3)
        assert False == SPOT_time(1.4, 0.3)
        assert True == SPOT_time(2.0, 0.3)

if __name__ == '__main__':
    unittest.main()

