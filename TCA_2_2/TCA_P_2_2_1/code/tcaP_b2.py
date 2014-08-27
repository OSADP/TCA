#standard
import time
import sys
import logging
from datetime import datetime as dt

#external
import pandas as pd

#TCA Libraries
from TCARandom import Random_generator
from TCALoadControl import ControlFiles
from TCADataStore import DataStorage
from TCAAlgorithm import TCA_Algorithm
from TCAFileReader import Trajectories
from TCAOutput import TCA_Output
from TCACore import Timer, logger
from TCARegions import Load_Regions



def vehColorParseList(vList, tp):

    global LastTP
    global Snapshots
    global PDMBuffer
    global BSMBuffer

    #print len(vList)
    vColorList = []
    x = 0.0
    y = 0.0

    if len(vList) == 0:
        LastTP = tp
        return vColorList

    pdm = False
    cellular_comm = False
    vehicle_list = []
                
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
        #print j
        
                    
        if vehType in CF.Control['PDMBSMDSRCVehicleTypes'] or vID in CF.Control['PDMBSMDSRCVehicleIDs']:
                pdm = True
                vehicle_list.append({
                            'vehicle_ID': vID,
                            'time' : tp,
                            'speed' : speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                            'accel_instantaneous' : accel * 100 / 2.54 / 12, #convert to ft/s^2
                            'location_x' : x,
                            'location_y' : y,
                            'link_name' : linkName,
                            'PDM_equipped' : True,
                            'BSM_equipped' : True,
                            'DSRC_enabled' : True,
                            'cellular_enabled' : False,
                            'dual_enabled' : False,
                })

        elif vehType in CF.Control['PDMBSMCellularVehicleTypes'] or vID in CF.Control['PDMBSMCellularVehicleIDs']:
                pdm = True
                cellular_comm = True
                vehicle_list.append({
                            'vehicle_ID': vID,
                            'time' : tp,
                            'speed' : speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                            'accel_instantaneous' : accel * 100 / 2.54 / 12, #convert to ft/s^2
                            'location_x' : x,
                            'location_y' : y,
                            'link_name' : linkName,
                            'PDM_equipped' : True,
                            'BSM_equipped' : True,
                            'DSRC_enabled' : False,
                            'cellular_enabled' : True,
                            'dual_enabled' : False,
                })
        elif vehType in CF.Control['PDMBSMDualCommVehicleTypes'] or vID in CF.Control['PDMBSMDualCommVehicleIDs']:
                cellular_comm = True
                pdm = True
                vehicle_list.append({
                            'vehicle_ID': vID,
                            'time' : tp,
                            'speed' : speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                            'accel_instantaneous' : accel * 100 / 2.54 / 12, #convert to ft/s^2
                            'location_x' : x,
                            'location_y' : y,
                            'link_name' : linkName,
                            'PDM_equipped' : True,
                            'BSM_equipped' : True,
                            'DSRC_enabled' : False,
                            'cellular_enabled' : False,
                            'dual_enabled' : True,
                })

        elif vehType in CF.Control['BSMDSRCVehicleTypes'] or vID in CF.Control['BSMDSRCVehicleIDs']:
                vehicle_list.append({
                            'vehicle_ID': vID,
                            'time' : tp,
                            'speed' : speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                            'accel_instantaneous' : accel * 100 / 2.54 / 12, #convert to ft/s^2
                            'location_x' : x,
                            'location_y' : y,
                            'link_name' : linkName,
                            'PDM_equipped' : False,
                            'BSM_equipped' : True,
                            'DSRC_enabled' : True,
                            'cellular_enabled' : False,
                            'dual_enabled' : False,
                })

        elif vehType in CF.Control['BSMCellularVehicleTypes'] or vID in CF.Control['BSMCellularVehicleIDs']:
                cellular_comm = True
                vehicle_list.append({
                            'vehicle_ID': vID,
                            'time' : tp,
                            'speed' : speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                            'accel_instantaneous' : accel * 100 / 2.54 / 12, #convert to ft/s^2
                            'location_x' : x,
                            'location_y' : y,
                            'link_name' : linkName,
                            'PDM_equipped' : False,
                            'BSM_equipped' : True,
                            'DSRC_enabled' : False,
                            'cellular_enabled' : True,
                            'dual_enabled' : False,
                })
        elif vehType in CF.Control['BSMDualCommVehicleTypes'] or vID in CF.Control['BSMDualCommVehicleIDs']:
                cellular_comm = True
                vehicle_list.append({
                            'vehicle_ID': vID,
                            'time' : tp,
                            'speed' : speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                            'accel_instantaneous' : accel * 100 / 2.54 / 12, #convert to ft/s^2
                            'location_x' : x,
                            'location_y' : y,
                            'link_name' : linkName,
                            'PDM_equipped' : False,
                            'BSM_equipped' : True,
                            'DSRC_enabled' : False,
                            'cellular_enabled' : False,
                            'dual_enabled' : True,
                })

        elif vehType in CF.Control['PDMDSRCVehicleTypes'] or vID in CF.Control['PDMDSRCVehicleIDs']:
            pdm = True
            vehicle_list.append({
                        'vehicle_ID': vID,
                        'time' : tp,
                        'speed' : speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                        'accel_instantaneous' : accel * 100 / 2.54 / 12, #convert to ft/s^2
                        'location_x' : x,
                        'location_y' : y,
                        'link_name' : linkName,
                        'PDM_equipped' : True,
                        'BSM_equipped' : False,
                        'DSRC_enabled' : True,
                        'cellular_enabled' : False,
                        'dual_enabled' : False,
            })

        elif vehType in CF.Control['PDMCellularVehicleTypes'] or vID in CF.Control['PDMCellularVehicleIDs']:
                pdm = True
                cellular_comm = True
                vehicle_list.append({
                            'vehicle_ID': vID,
                            'time' : tp,
                            'speed' : speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                            'accel_instantaneous' : accel * 100 / 2.54 / 12, #convert to ft/s^2
                            'location_x' : x,
                            'location_y' : y,
                            'link_name' : linkName,
                            'PDM_equipped' : True,
                            'BSM_equipped' : False,
                            'DSRC_enabled' : False,
                            'cellular_enabled' : True,
                            'dual_enabled' : False,
                })
        elif vehType in CF.Control['PDMDualCommVehicleTypes'] or vID in CF.Control['PDMDualCommVehicleIDs']:
                pdm = True
                cellular_comm = True
                vehicle_list.append({
                            'vehicle_ID': vID,
                            'time' : tp,
                            'speed' : speed * 100 / 2.54 / 12 / 5280 * 3600, #convert m/s to mph
                            'accel_instantaneous' : accel * 100 / 2.54 / 12, #convert to ft/s^2
                            'location_x' : x,
                            'location_y' : y,
                            'link_name' : linkName,
                            'PDM_equipped' : True,
                            'BSM_equipped' : False,
                            'DSRC_enabled' : False,
                            'cellular_enabled' : False,
                            'dual_enabled' : True,
                })


    if len(vehicle_list) == 0:
        return
        #LastTP = tp
        #return vColorList

    df = pd.DataFrame(vehicle_list)

    Algorithm.BSMBuffer = {}

    timeStep = tp - LastTP
        
    tbl.update(tp, df,RandomGen, CF,TCA_version = 'vissim', time_step = timeStep)

        
    #Algorithm.CheckSnapshot(tbl.df, timeStep, tp, CF)
    if CF.Control['RegionsFile'] is not None:
        Algorithm.CheckRegion(tbl.df, tp, CF, R)

    ## ?? CheckBrakes
    Algorithm.CheckBrakes(tbl.df, CF)

    if tp % 1 == 0:
        checkPDM = True
    else:
        checkPDM = False

    if checkPDM and pdm:
        Algorithm.CheckPDMSnapshot(tbl.df, timeStep, tp, CF, R)

    Algorithm.CheckDSRC(tbl.df, CF, checkPDM, pdm, tp, R)

    if cellular_comm:
        Algorithm.CheckCellular(tbl.df, CF, RandomGen, checkPDM, pdm, tp, R)

    if checkPDM:
        Algorithm.PSNCheck(tbl.df, tp, RandomGen, CF)

    if len(Algorithm.BSMs) >= Algorithm.BSM_limit:
        df_BSMs = pd.DataFrame(Algorithm.BSMs)
        df_BSMs.to_csv(path_or_buf =CF.Control["BSMTransFile"], index=False,  mode='a')
        Algorithm.BSMs = []

    #vColorList.append(vID)

    #Go through vehicles and change the color if a snapshot is generated
    if changecolor:                          
        color_display_time = CF.Control['ColorDisplayDuration']

        numVehInPy = 0
        for vehicle in vehicle_list:                                
            select = (tbl.df['vehicle_ID'] == vehicle['vehicle_ID'])
            
            vColorList.append(vehicle['vehicle_ID'])
            vColorList.append(vehicle['link_name'])
            numVehInPy = numVehInPy + 1 

            diff_time = tbl.df['time_of_start_snapshot'][select] - tp + color_display_time     
                                
            if (tbl.df['time_of_start_snapshot'][select] - tp + color_display_time > 0):
                color = 1   #Change color to green for start PDM SS

            elif (tbl.df['time_of_last_stop'][select] - tp + color_display_time + 3 > 0):
                color = 2   #Change color to orange for stop PDM SS

            elif ((not tbl.df['dsrc_transmit_pdm'][select]) and (tbl.df['time_of_last_transmit'][select] - tp + color_display_time > 0)):
                color = 3 #Change to black for PDM DSRC transmission

            elif ((not tbl.df['dsrc_transmit_pdm'][select]) and (tbl.df['time_of_last_transmit'][select] - tp + color_display_time > 0)):
                color = 6 #Change to light blue for PDM cellular transmission

            elif (tbl.df['time_of_periodic_snapshot'][select] - tp + color_display_time > 0):
                color = 4    #Change color to purple for periodic PDM

            elif (tbl.df['BSM_equipped'][select] and tbl.df['PDM_equipped'][select]):
                color = 7 #Change to yellow for Dual PDM-BSM vehicles

            elif ((not tbl.df['BSM_equipped'][select]) and tbl.df['PDM_equipped'][select]):
                color = 8 #Change to teal for PDM-only vehicles

            elif (tbl.df['BSM_equipped'][select]):
                color = 0   #Change BSM-only vehicles to blue

            else :
                color = 5 #Change color to white
                
            vColorList.append(color)

            vColorList.append(checkPDM)

    LastTP = tp
    #vColorList.append(numVehInPy)
        

##        for vehicle in vehicle_list: 
##                
##            vColorList.append(vehicle['vehicle_ID'])
##            vColorList.append(vehicle['link_name'])
##            vColorList.append(color)
                    
##    for ID in Algorithm.Buffer.ActiveBuffers.keys():
##        Algorithm.Buffer.ClearBuffer(ID, tp, Algorithm.Snapshots)
##    output.WriteSSList(Algorithm.Snapshots, CV)

    return vColorList

def finish_up(LastTP):
    
    global Algorithm
    global output
    global Snapshots
    global Buffer
    global CF
    
#    Algorithm = TCA_Algorithm(CV)
    if len(Algorithm.BSMs) > 0:
        df_BSMs = pd.DataFrame(Algorithm.BSMs)
        df_BSMs.to_csv(path_or_buf =CF.Control["BSMTransFile"], index=False,  mode='a')
        # output.WriteBSMList(Algorithm.BSMs, CF, R)

    if len(Algorithm.PDMs) > 0:
        for ID in Algorithm.PDMBuffer.ActiveBuffers.keys():
            Algorithm.PDMBuffer.ClearBuffer(ID, LastTP + 2, Algorithm.PDMs, 2, -1, -1)
        output.WriteSSList(Algorithm.PDMs, CF)

#NOTE Create a procedure to start up all key items.
def start_up(inputFPath):

    global tbl
    global LastTP
    global CF
    global RandomGen
    global Algorithm
    global output
    global logger
    global R
    global changecolor

    changecolor = True
    LastTP = 0
    #inputFPath = inputFPath + "\"
    inputf = inputFPath + "TCAinput.xml"
    #inputf = "C:\Users\Public\paramics\data\BSM\colorDemo\code\TCA22_test\TCAinput.xml"

    #NOTE new class for storing Global variables
    CF = ControlFiles(inputFPath, inputf, TCA_version = 'vissim')
    CF.Load_files()

    CF.Control['AccelColumn'] = True

    if CF.Control['RegionsFile'] is not None:
        R = Load_Regions(CF.Control['RegionsFile'],CF.Control['Seed'])
    else:
        R = None

    if CF.Error_count() > 0:
        logging.critical("Errors in the control and/or strategy file, see TCA_Input_Summary.csv file for details")
        sys.exit()

    output = TCA_Output(CF,R)

    #NOTE New Random number generator with seed value for all Random number values
    RandomGen = Random_generator(CF.Control['Seed'])
    RandomGen.add_generator_int('GapDistance', CF.Strategy["GapMinDistance"], CF.Strategy["GapMaxDistance"])
    RandomGen.add_generator_int('GapTimeout', CF.Strategy["GapMinTime"], CF.Strategy["GapMaxTime"])
    RandomGen.add_generator_int('psn', 0, 32767)  #range based on J2735
    RandomGen.add_generator_int('LossPercent', 1, 100)


    #NOTE is a new class that will also loads the RSE file when it starts
    #the RSE file is location of the Road Side Equipment in the network and
    #will need to be modified for your network
    Algorithm = TCA_Algorithm(CF)


    #create Table
    #NOTE this list is a list of all vehicle IDS.  For VISSIM Vehicles start at 1 and move forward
    #So we can use a range value like the comment out line below
    tbl = DataStorage(list(xrange(int(CF.Control['NumberEquippedVehicles']))), Regions = R, accel_included = True, time_step = 0.1)


    #NOTE total number of time periods
    #This is not used for VISSIM version because the processTimestep runs for every
    #time period so all we need is   app.run() to start that process
    total_TP = 2

    vehicle_list = []
    #NOTE runs for each time period
    for tp in range(total_TP):
        #NOTE need to create a list of vehicles for the give time period
        
        vehicle_list = [
            [2,tp,0,0, 34.2, 54.3, 'Link1',1],
            [3,tp,0,0, 23.2, 54.3, 'Link1',1],
            [5,tp,0,0, 45.6, 26.8, 'Link4',1],
        ]


        vehColorParseList(vehicle_list, tp)


