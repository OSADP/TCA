#standard
import sys
import time

#external
import pandas as pd

#TCA
from TCARandom import Random_generator
from TCALoadControl import ControlFiles
from TCAAlgorithm import TCA_Algorithm
from TCAFileReader import Trajectories
from TCAOutput import TCA_Output
from TCACore import Timer, logger, report_errors
from TCARegions import Load_Regions
from TCASpacePartitioning import Location_Tree
from TCANetData import CLNetData


def main():
    """
    TCA main procedure

    """

    if len(sys.argv) == 2:
        input_file = sys.argv[1]
    else:
        input_file = "TCAinput.xml"

    program_st = time.time()

    CF = ControlFiles(input_file)
    CF.Load_files()

    RandomGen = Random_generator(CF.Control['Seed'])

    if CF.Control["FileType"] == "VISSIM":
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
       RSE_Tree =Location_Tree(RSEs.RSEList, CF.Strategy["MinRSERange"])
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

    RandomGen.add_generator_int('GapDistance', CF.Strategy["GapMinDistance"], CF.Strategy["GapMaxDistance"])
    RandomGen.add_generator_int('GapTimeout', CF.Strategy["GapMinTime"], CF.Strategy["GapMaxTime"])
    RandomGen.add_generator_int('psn', 0, 32767)  #range based on J2735
    RandomGen.add_generator_int('LossPercent', 1, 100)
    RandomGen.add_generator_int('TypePercent', 1, 100)


    trajectory_file = Trajectories(CF.Control['TrajectoryFileName'], CF.Control['OutputLevel'], CF.Control["FileType"])
    output_files = TCA_Output(CF, Regions)

    Algorithm = TCA_Algorithm(CF, RSEs, RSE_Tree, RandomGen, Regions, SPOT_Tree)

    LastTP = 0.0
    headerBSM = True
    headerCAM = True

    for tp, vehicles in trajectory_file.read_by_tp(CF):
        Algorithm.BSMBuffer = {}

        if CF.Control["OutputLevel"] > 0:
            if tp % 1000 == 0:
               logger.info("Time Step: %d" % (tp))

        Algorithm.tbl.remove_non_active_vehicles(vehicles)

        for vehicle in vehicles:

            veh_data = Algorithm.pull_veh_data(vehicle, tp)

            #if vehicle equipped
            if veh_data != None:

                if veh_data['BSM_equipped']:
                    if CF.Control['RegionsFile'] is not None:
                        Algorithm.CheckRegion(veh_data, tp)
                    Algorithm.CheckBrakes(veh_data)

                #if SPOT equipped
                if veh_data['SPOT_equipped']:
                    Algorithm.CheckSPOT(veh_data, tp)
                    Algorithm.CheckSPOTdevice(veh_data, tp)

                #if PDM equipped
                if (tp % 1 ==0) and (veh_data['PDM_equipped']):
                    Algorithm.CheckPDMSnapshot(veh_data, tp)

                if veh_data['DSRC_enabled']:
                    Algorithm.CheckDSRC(veh_data, tp)

                Algorithm.CheckCellular(veh_data, tp)

                if (tp % 1 ==0) and (veh_data['PDM_equipped']):
                    Algorithm.PSNCheck(veh_data, tp)

                LastTP = tp

                if len(Algorithm.BSMs) >= Algorithm.BSM_limit:
                    df_BSMs = pd.DataFrame(Algorithm.BSMs)
                    df_BSMs = df_BSMs.sort(['transtime', 'Vehicle_ID'])
                    df_BSMs = df_BSMs.drop('Vehicle_ID', axis = 1)
                    df_BSMs['avg_accel'] = df_BSMs['avg_accel'].fillna(-9999.0)
                    df_BSMs['heading'] = df_BSMs['heading'].fillna(-9999.0)
                    df_BSMs['avg_accel'] = df_BSMs['avg_accel'].map('{:.3f}'.format)
                    df_BSMs['spd'] = df_BSMs['spd'].map('{:.3f}'.format)
                    df_BSMs['heading'] = df_BSMs['heading'].map('{:.3f}'.format)

                    df_BSMs.to_csv(path_or_buf =CF.Control["BSMTransFile"],
                                   index=False,
                                   mode='a',
                                   header = headerBSM,
                                    )
                    headerBSM = False
                    Algorithm.BSMs = []

                if len(Algorithm.CAMs) >= Algorithm.CAM_limit:
                    col = ['protocolVersion','messageID','stationID','generationDeltaTime','stationType',
                           'latitude','longitude','semiMajorConfidence','semiMinorConfidence','altitudeValue','heading',
                           'headingConfidence','speed','speedConfidence','driveDirection','longitudinalAcceleration',
                           'curvatureValue','curvatureConfidence','yawRateValue','yawRateConfidence','vehicleLengthValue',
                           'vehicleLengthConfidence','vehicleWidth']
                    df_CAMs = pd.DataFrame(Algorithm.CAMs, columns=col)
                    df_CAMs['spd'] = df_CAMs['spd'].map('{:.3f}'.format)
                    df_CAMs['yawRateValue'] = df_CAMs['yawRateValue'].fillna(32767)
                    df_CAMs['heading'] = df_CAMs['heading'].fillna(360)
                    df_CAMs = df_CAMs.sort(['generationDeltaTime'])
                    df_CAMs.to_csv(path_or_buf =CF.Control["CAMTransFile"], index=False,  mode='a', header = headerCAM)
                    headerCAM = False
                    Algorithm.CAMs = []

                Algorithm.tbl.previous_values(veh_data)

    if len(Algorithm.BSMs) > 0 :
        df_BSMs = pd.DataFrame(Algorithm.BSMs)
        df_BSMs = df_BSMs.sort(['transtime', 'Vehicle_ID'])
        df_BSMs = df_BSMs.drop('Vehicle_ID', axis = 1)
        df_BSMs['avg_accel'] = df_BSMs['avg_accel'].fillna(-9999.0)
        df_BSMs['heading'] = df_BSMs['heading'].fillna(-9999.0)
        df_BSMs['avg_accel'] = df_BSMs['avg_accel'].map('{:.3f}'.format)
        df_BSMs['spd'] = df_BSMs['spd'].map('{:.3f}'.format)
        df_BSMs['heading'] = df_BSMs['heading'].map('{:.3f}'.format)
        df_BSMs.to_csv(path_or_buf =CF.Control["BSMTransFile"],
                       index=False,
                       mode='a',
                       header = headerBSM,
                       )

    if len(Algorithm.CAMs) > 0 :
        col = ['protocolVersion','messageID','stationID','generationDeltaTime','stationType','latitude',
               'longitude','semiMajorConfidence','semiMinorConfidence','altitudeValue','heading','headingConfidence',
               'speed','speedConfidence','driveDirection','longitudinalAcceleration','curvatureValue','curvatureConfidence',
               'yawRateValue','yawRateConfidence','vehicleLengthValue','vehicleLengthConfidence','vehicleWidth']
        df_CAMs = pd.DataFrame(Algorithm.CAMs, columns=col)
        df_CAMs['speed'] = df_CAMs['speed'].map('{:.3f}'.format)
        df_CAMs['yawRateValue'] = df_CAMs['yawRateValue'].fillna(32767)
        df_CAMs['heading'] = df_CAMs['heading'].fillna(360)
        df_CAMs = df_CAMs.sort(['generationDeltaTime'])
        df_CAMs.to_csv(path_or_buf =CF.Control["CAMTransFile"], index=False,  mode='a', header = headerCAM)


    if len(Algorithm.PDMs) > 0 :
        for ID in Algorithm.PDMBuffer.ActiveBuffers.keys():
            Algorithm.PDMBuffer.ClearBuffer(vehicleID = ID, locT = LastTP + 2, Snapshots = Algorithm.PDMs, reason = 2, transmitted_to = -1, transTime = -1)
        output_files.WriteSSList(Algorithm.PDMs, CF)

    if len(Algorithm.TravelSPOTmsgs) > 0:
        output_files.WriteSPOTList(Algorithm.TravelSPOTmsgs, Algorithm.BehaviorSPOTmsgs, CF)

    if CF.Control["OutputLevel"] > 0:
        Algorithm.tbl.list_veh_counts()

    if CF.Control["OutputLevel"] > 0:
        ed_time = time.time()
        logger.info("End time %s (%f)" % (time.strftime('%X', time.localtime(ed_time)), (ed_time - program_st) ))
        logger.info("*******************  End Program  *******************")

    del Algorithm



if __name__ == '__main__':
    main()