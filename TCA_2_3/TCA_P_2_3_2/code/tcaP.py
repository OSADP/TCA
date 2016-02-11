#standard
import time
import sys
from datetime import datetime as dt

#external
import pandas as pd

#TCA
from TCARandom import Random_generator
from TCALoadControl import ControlFiles
from TCAAlgorithm import TCA_Algorithm
from TCAFileReader import Trajectories
# from TCAOutput import TCA_Output
from TCACore import Timer, logger, report_errors, clear_old_files
from TCARegions import Load_Regions
from TCARegions import Region
from TCASpacePartitioning import Location_Tree
from TCANetData import CLNetData


def vehColorParseList(vList, tp):

    global LastTP
    global Snapshots
    global PDMBuffer
    global headerBSM
    global headerCAM

    headerBSM = True
    headerCAM = True

    vColorList = []
    x = 0.0
    y = 0.0

    if len(vList) == 0:
        LastTP = tp
        return vColorList


    if CF.Control["OutputLevel"] > 0:
        if tp % 1000 == 0:
           logger.info("Time Step: %d" % (tp))


    vehicles_ids = []
    for i in range(len(vList)):
        tempVList = []
        tempVList = vList[i]
        vID = tempVList[0]
        active_veh = {'vehicle_ID' : vID }
        vehicles_ids.append(active_veh)

        linkName = tempVList[6]
        vehType = tempVList[7]

    Algorithm.tbl.remove_non_active_vehicles(vehicles_ids)

    timeStep = tp - LastTP


    vehicles_list = []
                
    for i in range(len(vList)):

        tempVList = []
        tempVList = vList[i]
        #print tempVList
        #j = i%6
        vID = tempVList[0]
        tp = tempVList[1]
        speed= tempVList[2]
        accel= tempVList[3]
        x = tempVList[4]
        y = tempVList[5]
        # Copy vehicle link name 
        linkName = tempVList[6]
        vehType = tempVList[7]
        linkID = tempVList[8]
        #print j
        
  
        vehicle = {
                'vehicle_ID': vID,
                'time': float(tp),
                'type': vehType,
                'accel_instantaneous': float(accel * 100 / 2.54 / 12), #convert m/s^2 to ft/s^2
                'speed': float(speed * 100 / 2.54 / 12 / 5280 * 3600),  #convert m/s to mph
                'location_x': float(x * 100 / 2.54 / 12), #convert meters to feet
                'location_y': float(y * 100 / 2.54 / 12), #convert meters to feet
                'link' : linkID,
                'link_name' : linkName
                }
        vehicles_list.append(vehicle)

    vehicles_data = Algorithm.pull_veh_data(vehicles_list, tp)
    range_data = RSE_Tree.find_ranges(vehicles_data)

    for i,veh_data in enumerate(vehicles_data):

         #veh_data = Algorithm.pull_veh_data(vehicle, tp)

       #if vehicle equipped
        if veh_data is not None:

            if veh_data['BSM_equipped']:
                if CF.Control['RegionsFile'] is not None:
                    Regions.CheckRegions(veh_data, tp)
                Algorithm.BSM.CheckBrakes(veh_data)

            #if SPOT equipped
            if veh_data['SPOT_equipped']:
                Algorithm.SPOT.CheckMessage(veh_data, tp)
                Algorithm.SPOT.CheckRange(veh_data, tp)

            #if PDM equipped
            if (tp % 1 ==0) and (veh_data['PDM_equipped']):
                Algorithm.PDM.CheckMessage(veh_data, tp)

            if veh_data['DSRC_enabled']:
                Algorithm.CheckDSRC(veh_data, tp, range_data)

            
            Algorithm.CheckCellular(veh_data, tp)


            if (tp % 1 ==0) and (veh_data['PDM_equipped']):
                Algorithm.PDM.PSNCheck(veh_data, tp)

            if veh_data['BSM_equipped']:
                Algorithm.BSM.tmp_ID_check(veh_data, tp)

            if changecolor:
                color_display_time = CF.Control['ColorDisplayDuration']
                vColorList.append(veh_data['vehicle_ID'])
                vColorList.append(veh_data['link_name'])
                #vColorList.append(veh_data['link'])

                color = change_vehicle_color(veh_data, tp, color_display_time)
                vColorList.append(color)
                vColorList.append(veh_data['vehicle_type'])


            Algorithm.BSM.Write()
            Algorithm.CAM.Write()

            Algorithm.tbl.previous_values(veh_data)


        LastTP = tp


    return vColorList

#----------------------------------------------------------------------
def change_vehicle_color(veh_data, tp, color_display_time):

    if veh_data['PDM_equipped']:
        if (veh_data['time_of_start_snapshot'] - tp + color_display_time > 0):
            color = 1   #Change color to green for start PDM SS
            return color

        elif (veh_data['time_of_last_stop'] - tp + color_display_time > 0):
            color = 2   #Change color to orange for stop PDM SS
            return color

        elif (veh_data['prev_time_PDM_dsrc_transmit'] - tp + color_display_time > 0):
            color = 3 #Change to black for PDM DSRC transmission
            return color

        elif (veh_data['prev_time_PDM_cellular_transmit'] - tp + color_display_time > 0):
            color = 6 #Change to light blue for PDM cellular transmission
            return color

        elif (veh_data['time_of_periodic_snapshot'] - tp + color_display_time > 0):
            color = 4    #Change color to purple for periodic PDM
            return color

        elif not veh_data['BSM_equipped']:
            color = 8 #Change to white for PDM-only vehicles
            return color

        elif veh_data['BSM_equipped']:
            color = 7 #Change to white for Dual PDM-BSM vehicles
            return color

    if (veh_data['BSM_equipped']) and not veh_data['PDM_equipped']:
        color = 0   #Change BSM-only vehicles to blue
        return color

    if (veh_data['CAM_equipped']) and (veh_data['last_CAM_time'] != None):
        if (veh_data['last_CAM_time'] - tp + color_display_time > 0):
            color = 9 # orange "CAMTransColor"
            return color

    if (veh_data['SPOT_equipped']):
        if (veh_data['SPOT_accel_tp'] is not None or veh_data['SPOT_yawrate_tp'] is not None):
            color = 10 # violet SpotBehaviorColor"
            return color

        elif ((veh_data['prev_tp_travel_SPOT'] is not None) and (veh_data['prev_tp_travel_SPOT'] - tp + color_display_time > 0)):
            color = 11 # blue "SpotTravelColor"
            return color

        elif ((veh_data['SPOT_trans_tp'] is not None) and (veh_data['SPOT_trans_tp'] - tp + color_display_time > 0)):
            color = 12 # yellow "SpotTransColor"
            return color

    color = 5 #Change color to white


    return color

def finish_up(LastTP):
    
    global tbl
    global CF
    global RandomGen
    global Algorithm
    global output_file
    global logger
    global Regions
    global RSE_Tree
    global headerBSM
    global headerCAM
    
    if len(Algorithm.BSM.BSM_list) > 0 :
        Algorithm.BSM.Write(clear_buffer=True)

    if len(Algorithm.CAM.CAM_list) > 0 :
        Algorithm.CAM.Write(clear_all=True)

    if len(Algorithm.PDM.PDM_list) > 0 :
        Algorithm.PDM.Write(clear_buffer = True, LastTP = LastTP)

    if len(Algorithm.SPOT.Travelmsgs) > 0:
        Algorithm.SPOT.Write(CF, clear_all=True)

    if CF.Control["OutputLevel"] > 0:
        Algorithm.tbl.list_veh_counts()


    del Algorithm


#NOTE Create a procedure to start up all key items.
def start_up(inputFPath):


 
    global tbl
    global LastTP
    global CF
    global RandomGen
    global Algorithm
    global output_file
    global logger
    global Regions
    global RSE_Tree
    global headerBSM
    global headerCAM
    global changecolor

    LastTP = 0
    headerBSM = True
    headerCAM = True 

    inputf = inputFPath + "TCAinput.xml" #"TCAinput_SPOT_CAM.xml" #

    CF = ControlFiles(inputf, TCA_version = 'paramics')
    CF.Load_files()

    if CF.Error_count() > 0:
        logging.critical("Errors in the control and/or strategy file, see TCA_Input_Summary.csv file for details")
        sys.exit()

    changecolor = CF.Control['ColorDisplay']
    if changecolor == 'False':
        changecolor = 0

    changecolor = True

    CF.Control['AccelColumn'] = True

    if CF.Control['RegionsFile'] is not None:
        unit_conversion = 100 / 2.54 / 12
        Regions = Load_Regions(CF.Control['RegionsFile'],CF.Control['Seed'],unit_conversion)
        print CF.Control['RegionsFile']
        #print "Loading Regions File %s" % CF.Control['RegionsFile']
    else:
        Regions = None

    if CF.Control["RSELocationFile"] is not None:
        unit_conversion = 100 / 2.54 / 12
        RSEs = CLNetData(unit_conversion)
        errors = RSEs.RSELoad(CF.Control["RSELocationFile"], CF)
        report_errors(errors)
        RSE_Tree = Location_Tree(RSEs.RSEList, CF.Strategy["MinRSERange"])
    else:
        RSEs = None
        RSE_Tree = None

    if CF.Control["SPOTLocationFile"] is not None:
        SPOTdevices = CLNetData(unit_conversion)
        errors = SPOTdevices.SPOTLoad(CF.Control["SPOTLocationFile"], CF)
        report_errors(errors)
        SPOT_Tree =Location_Tree(SPOTdevices.SPOTList, CF.Strategy["SPOTdeviceRange"])
    else:
        SPOTdevices = None
        SPOT_Tree = None

    clear_old_files(CF)

    Algorithm = TCA_Algorithm(CF, RSEs, RSE_Tree, CF.Control['Seed'], Regions, SPOT_Tree)


    #NOTE total number of time periods
    #This is not used for VISSIM version because the processTimestep runs for every
    #time period so all we need is   app.run() to start that process
    total_TP = 2

    vehicle_list = []
    #NOTE runs for each time period
    for tp in range(total_TP):
        #NOTE need to create a list of vehicles for the given time period
        
        vehicle_list = [
            [2,tp,0,0, 34.2, 54.3, 'Link1',1,2],
            [3,tp,0,0, 23.2, 54.3, 'Link1',1,3],
            [5,tp,0,0, 45.6, 26.8, 'Link4',1,2],
        ]


        vehColorParseList(vehicle_list, tp)
