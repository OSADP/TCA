
#standard
import sys
import time
import os

#TCA
from TCARandom import Random_generator
from TCALoadControl import ControlFiles
from TCAAlgorithm import TCA_Algorithm
from TCAFileReader import Trajectories
# from TCAOutput import TCA_Output
from TCACore import Timer, logger, report_errors, clear_old_files, write_default, write_default_didc, write_default_regions, control_values, strategy_values
from TCARegions import Load_Regions
from TCASpacePartitioning import Location_Tree
from TCANetData import CLNetData

import argparse

def main():
    """
    TCA main procedure

    """
    parser = argparse.ArgumentParser(description = 'The Trajectory Conversion Algorithm (TCA) Software is designed to test different strategies for producing, transmitting, and storing Connected \
        Vehicle information.The TCA reads in and uses vehicle trajectory information, Roadside Equipment (RSE) location information, cellular region information, event region information, and strategy \
        information to produce a series of snapshots that the vehicle would produce. Vehicles can be equipped to generate and transmit Probe Data Messages (PDMs), Basic Safety Messages (BSMs), ITS SPOT \
        messages, European CAM, or DIDC Basic Mobility Messages (BMMs) which can be transmitted by either Dedicated Short Range Communication (DSRC), cellular, or both.')
    parser.add_argument('input_file', help = 'TCA input file', default = 'TCAinput.xml', nargs = '?')
    parser.add_argument('--makeInput', help = 'Make input file with specified filename, strategy file(Default_Strategy.xml), DIDC file(Default_DIDC.xml), Regions File(Default_Regions.xml)')
    parser.add_argument('--makeStrategy', help = 'Make strategy file with specified filename')
    parser.add_argument('--makeDIDC', help = 'Make DIDC file with specified filename')
    parser.add_argument('--makeRegions', help = 'Make Regions file with specified filename')

    args = parser.parse_args()
    if args.makeInput or args.makeStrategy or args.makeDIDC or args.makeRegions:
        if args.makeInput:
            write_default(args.makeInput, 'ControlFile', control_values)
            write_default("Default_Strategy.xml", 'Strategy', strategy_values)
            write_default_regions('Default_Regions.xml')
            write_default_didc('Default_DIDC.xml')
        if args.makeStrategy:
            write_default(args.makeStrategy, 'Strategy', strategy_values)
        if args.makeDIDC:
            write_default_didc(args.makeDIDC)
        if args.makeRegions:
            write_default_regions(args.makeRegions)
        sys.exit()
    
    timer = Timer(enabled=False)
    timer.start('1_main')

    program_st = time.time()
    CF = ControlFiles(args.input_file)
    CF.Load_files()


    if CF.Control["FileType"] == "VISSIM" or CF.Control['FileType'] == 'VISSIM7':
        unit_conversion = 100 / 2.54 / 12 # Converts meters to ft (for x,y coordinates)
    else:
        unit_conversion = 1

    if CF.Control['RegionsFile'] is not None:
        Regions = Load_Regions(CF.Control['RegionsFile'], CF.Control['Seed'], unit_conversion)
        if CF.Control["OutputLevel"] > 0:
            logger.info("Loading Regions File %s" % CF.Control['RegionsFile'])
    else:
        Regions = None

    if CF.Control["RSELocationFile"] is not None:
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
        SPOT_Tree = Location_Tree(SPOTdevices.SPOTList, CF.Strategy["SPOTdeviceRange"])
    else:
        SPOT_Tree = None


    trajectory_file = Trajectories(CF.Control['TrajectoryFileName'], CF.Control['OutputLevel'], CF.Control["FileType"])

    clear_old_files(CF)

    Algorithm = TCA_Algorithm(CF, RSEs, RSE_Tree, CF.Control['Seed'], Regions, SPOT_Tree, link_included = CF.Control['Link_Included'])

    LastTP = 0.0

    # with open(curdir + 'time_testing.csv', 'wb') as time_f:
    #     time_f.write('time_period, active, BSMs, PDMs, buff_keys,  run_time, Update_time, CheckSnapshot, CheckDSRC, '
    #                  + 'CheckCellular, PSNCheck, alg_check_dsrc_select_vehicles, alg_check_dsrc_Find_RSE_Ranges, '
    #                  + 'alg_check_dsrc_Transmit\n')


    # ALGORITHM Step 9.0 Read One Timestep of Vehicles
    for tp, vehicles in trajectory_file.read_by_tp(CF):
        timer.start('tp')

        if CF.Control["OutputLevel"] > 0:
            if tp % 1000 == 0:
               logger.info("Time Step: %d" % (tp))

        # ALGORITHM Step 9.1 Account for Vehicles Not Seen in Last Time Step
        Algorithm.tbl.remove_non_active_vehicles(vehicles)

        # ALGORITHM Step 9.2 Initiate New Vehicles or Update Existing Vehicles from Active Vehicles List
        timer.start('2_Update_Table')
        vehicles_data = Algorithm.pull_veh_data(vehicles, tp)
        timer.stop('2_Update_Table')

        # ALGORITHM Step 9.3 Find RSEs in Range of Active Vehicles
        if RSE_Tree is not None:
        #     timer.start('2.1_Find_Range')
            range_data = RSE_Tree.find_ranges(vehicles_data)
        #     timer.stop('2.1_Find_Range')

        # ALGORITHM Step 9.4 Update Vehicle
        for veh_data in vehicles_data:

            #if vehicle equipped
            if veh_data is not None:

                # ALGORITHM Step 9.4.1 Update Brakes Info
                if veh_data['BSM_equipped'] or veh_data['DIDC_equipped'] :
                    # timer.start('9.4.1_CheckBrakes')
                    Algorithm.BSM.CheckBrakes(veh_data)
                    # timer.stop('9.4.1_CheckBrakes')

                # ALGORITHM Step 9.4.2 Update Event Region Variables    
                if CF.Control['RegionsFile'] is not None:
                    # timer.start('9.4.2_CheckRegions')
                    Regions.CheckRegions(veh_data, tp)
                    # timer.stop('9.4.2_CheckRegions')

                # ALGORITHM Step 9.4.3 Check ITS SPOT Triggers and Transmission
                if veh_data['SPOT_equipped']:
                #     timer.start('9.4.3_CheckITSSpot')
                    Algorithm.SPOT.CheckMessage(veh_data, tp) 
                    Algorithm.SPOT.CheckRange(veh_data, tp) 
                #     timer.stop('9.4.3_CheckITSSpot')

                # ALGORITHM Step 9.4.4 Check PDM Triggers
                if (tp % 1 ==0) and (veh_data['PDM_equipped']):
                    # timer.start('9.4.4_CheckPDMMessage')
                    Algorithm.PDM.CheckMessage(veh_data, tp) 
                    # timer.stop('9.4.4_CheckPDMMessage')

                # ALGORITHM Step 9.4.5 Check for DIDC Triggers
                if veh_data['DIDC_equipped']:
                    Algorithm.CheckDIDC(veh_data, tp)

                # ALGORITHM Step 9.4.6 Check for RSE Interaction
                if veh_data['DSRC_enabled'] and CF.Control['RSELocationFile'] != None:
                #     timer.start('9.4.6_CheckDSRC')
                    Algorithm.CheckDSRC(veh_data, tp, range_data)
                #     timer.stop('9.4.6_CheckDSRC')

                # ALGORITHM Step 9.4.7 Check for Cellular Interaction
                # timer.start('9.4.7_CheckCellular')
                Algorithm.CheckCellular(veh_data, tp)
                # timer.stop('9.4.7_CheckCellular')

                # ALGORITHM Step 9.4.8 Manage PSN and Privacy Gap initiation/expiration
                if (tp % 1 ==0) and (veh_data['PDM_equipped']):
                    # timer.start('8_PSNCheck')
                    Algorithm.PDM.PSNCheck(veh_data, tp)
                    # timer.stop('8_PSNCheck')

                # Update BSM Temporary IDs
                if veh_data['BSM_equipped']:
                    Algorithm.BSM.tmp_ID_check(veh_data, tp)

                Algorithm.BSM.Write()
                Algorithm.CAM.Write()
                Algorithm.BMM.Write()

                Algorithm.tbl.previous_values(veh_data)

        LastTP = tp
        timer.stop('tp')

    if len(Algorithm.BSM.BSM_list) > 0 :
        Algorithm.BSM.Write(clear_buffer=True)

    if len(Algorithm.CAM.CAM_list) > 0 :
        Algorithm.CAM.Write(clear_all=True)

    if len(Algorithm.BMM.BMM_list) > 0 :
        Algorithm.BMM.Write(clear_all=True)

    if len(Algorithm.PDM.PDM_list) > 0 :
        Algorithm.PDM.Write(clear_buffer=True, LastTP = LastTP)

    if len(Algorithm.SPOT.Travelmsgs) > 0:
        Algorithm.SPOT.Write(clear_all=True)

    if CF.Control["OutputLevel"] > 0:
        Algorithm.tbl.list_veh_counts()

    if CF.Control["OutputLevel"] > 0:
        ed_time = time.time()
        logger.info("End time %s (%f)" % (time.strftime('%X', time.localtime(ed_time)), (ed_time - program_st) ))
        logger.info("*******************  End Program  *******************")

    if timer.enabled:
        with open(curdir + 'timeit.csv', 'wb') as time_f:
            time_f.write(timer.header())
            time_f.write(timer.write())
            time_f.write('\n\n')
            time_f.write(Algorithm.tbl.timer.write())
            time_f.write('\n\n')
            time_f.write(Algorithm.timer.write())
            time_f.write('\n\n')
            time_f.write(Algorithm.BMM.timer.write())
            time_f.write('\n\n')
            if RSE_Tree is not None:
                time_f.write(RSE_Tree.timer.write())


    del Algorithm


if __name__ == '__main__':
    main()