#standard
import time
import sys
from datetime import datetime as dt

#external
import c2x
import pandas as pd

#TCA
from TCARandom import Random_generator
from TCALoadControl import ControlFiles
from TCAAlgorithm import TCA_Algorithm
from TCAFileReader import Trajectories
from TCAOutput import TCA_Output
from TCACore import logger, report_errors
from TCARegions import Load_Regions
from TCASpacePartitioning import Location_Tree
from TCANetData import CLNetData


#============================================================================
class C2X_tca (c2x.ApplicationBase):
    def __init__ (self, Debugger):
        """Constructor, needs to call the base-class constructor explicitely,
        otherwise c2x.run() will complain about non-matching signature."""

        c2x.ApplicationBase.__init__ (self)
        print "\nc2x initialized"


    def processTimestep (self):
        """This method is called every timestep for each class derived from
        c2x.ApplicationBase which is started with the <run()> function.
        TCA currently only runs every second
        VISSIM runs every tenth of a second
        """

        try:
            global vissimtimeit

            if not vissimtimeit:
                global LastTP
                global Snapshots
                global PDMBuffer
                global BSMBuffer
                global headerBSM
                global headerCAM

                tp = c2x.getCurrentTime()
                headerBSM = True
                headerCAM = True

                vehicles = c2x.getVehicles()

                if len (vehicles) == 0:
                    LastTP = tp
                    return

                Algorithm.BSMBuffer = {}

                if CF.Control["OutputLevel"] > 0:
                    if tp % 1000 == 0:
                       logger.info("Time Step: %d" % (tp))

                vehicles_ids = []
                for veh in vehicles:
                    active_veh = {'vehicle_ID' : veh.ID }
                    vehicles_ids.append(active_veh)


                Algorithm.tbl.remove_non_active_vehicles(vehicles_ids)

                timeStep = tp - LastTP

                for veh in vehicles:
                    vehicle = {
                            'vehicle_ID': veh.ID,
                            'time': float(tp),
                            'type': veh.TypeID,
                            'accel_instantaneous': float(veh.Acceleration * 100 / 2.54 / 12), #convert m/s^2 to ft/s^2
                            'speed': float(veh.Speed * 100 / 2.54 / 12 / 5280 * 3600),  #convert m/s to mph
                            'location_x': float(veh.Position.X * 100 / 2.54 / 12), #convert meters to feet
                            'location_y': float(veh.Position.Y * 100 / 2.54 / 12), #convert meters to feet
                            }

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

                        if changecolor:
                            color_display_time = CF.Control['ColorDisplayDuration']
                            change_vehicle_color(veh, veh_data, tp, color_display_time)

                        LastTP = tp

                        if len(Algorithm.BSMs) >= Algorithm.BSM_limit:
                            df_BSMs = pd.DataFrame(Algorithm.BSMs)
                            df_BSMs = df_BSMs.sort(['transtime', 'Vehicle_ID'])
                            df_BSMs = df_BSMs.drop('Vehicle_ID', axis = 1)
                            df_BSMs['avg_accel'] = df_BSMs['avg_accel'].fillna(-9999.00)
                            df_BSMs['heading'] = df_BSMs['heading'].fillna(-9999.00)
                            df_BSMs['avg_accel'] = df_BSMs['avg_accel'].map(lambda x: '%.3f' % x) 
                            df_BSMs['instant_accel'] = df_BSMs['instant_accel'].map(lambda x: '%.3f' % x) 
                            df_BSMs['spd'] = df_BSMs['spd'].map(lambda x: '%.3f' % x) 
                            df_BSMs['heading'] = df_BSMs['heading'].map(lambda x: '%.3f' % x) 

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
                            df_CAMs['spd'] = df_CAMs['spd'].map(lambda x: '%.3f' % x) 
                            df_CAMs['yawRateValue'] = df_CAMs['yawRateValue'].fillna(32767)
                            df_CAMs['heading'] = df_CAMs['heading'].fillna(360)
                            df_CAMs = df_CAMs.sort(['generationDeltaTime'])
                            df_CAMs.to_csv(path_or_buf =CF.Control["CAMTransFile"], index=False,  mode='a', header = headerCAM)
                            headerCAM = False
                            Algorithm.CAMs = []

                        Algorithm.tbl.previous_values(veh_data)


        except:
            raise
            time.sleep(1000)

#----------------------------------------------------------------------
def change_vehicle_color(vehicle, veh_data, tp, color_display_time):

    if (veh_data['time_of_start_snapshot'] - tp + color_display_time > 0):
        vehicle.setColor(CF.Control["PDMStartColor"][0],CF.Control["PDMStartColor"][1],CF.Control["PDMStartColor"][2]) 

    elif (veh_data['time_of_last_stop'] - tp + color_display_time > 0):
        vehicle.setColor(CF.Control["PDMStopColor"][0],CF.Control["PDMStopColor"][1],CF.Control["PDMStopColor"][2])   

    elif (veh_data['prev_time_PDM_dsrc_transmit'] - tp + color_display_time > 0):
        vehicle.setColor(CF.Control["PDMDSRCTransColor"][0],CF.Control["PDMDSRCTransColor"][1],CF.Control["PDMDSRCTransColor"][2]) 

    elif (veh_data['prev_time_PDM_cellular_transmit'] - tp + color_display_time > 0):
        vehicle.setColor(CF.Control["PDMCellularTransColor"][0],CF.Control["PDMCellularTransColor"][1],CF.Control["PDMCellularTransColor"][2])

    elif (veh_data['time_of_periodic_snapshot'] - tp + color_display_time > 0):
        vehicle.setColor(CF.Control["PDMPeriodicColor"][0],CF.Control["PDMPeriodicColor"][1],CF.Control["PDMPeriodicColor"][2])  

    elif (veh_data['BSM_equipped'] and veh_data['PDM_equipped']):
        vehicle.setColor(CF.Control["DualPDMBSMColor"][0],CF.Control["DualPDMBSMColor"][1],CF.Control["DualPDMBSMColor"][2]) 

    elif ((not veh_data['BSM_equipped']) and veh_data['PDM_equipped']):
        vehicle.setColor(CF.Control["PDMDefaultColor"][0],CF.Control["PDMDefaultColor"][1],CF.Control["PDMDefaultColor"][2]) 

    elif (veh_data['BSM_equipped']):
        vehicle.setColor(CF.Control["BSMDefaultColor"][0],CF.Control["BSMDefaultColor"][1],CF.Control["BSMDefaultColor"][2])   

    elif (veh_data['CAM_equipped'] and (veh_data['last_CAM_time'] - tp + color_display_time > 0)):
        vehicle.setColor(CF.Control["CAMTransColor"][0],CF.Control["CAMTransColor"][1],CF.Control["CAMTransColor"][2])

    elif (veh_data['SPOT_equipped']):
        if (veh_data['SPOT_accel_tp'] is not None or veh_data['SPOT_yawrate_tp'] is not None):
            vehicle.setColor(CF.Control["SpotBehaviorColor"][0],CF.Control["SpotBehaviorColor"][1],CF.Control["SpotBehaviorColor"][2])

        elif ((veh_data['prev_tp_travel_SPOT'] is not None) and (veh_data['prev_tp_travel_SPOT'] - tp + color_display_time > 0)):
            vehicle.setColor(CF.Control["SpotTravelColor"][0],CF.Control["SpotTravelColor"][1],CF.Control["SpotTravelColor"][2])

        elif ((veh_data['SPOT_trans_tp'] is not None) and (veh_data['SPOT_trans_tp'] - tp + color_display_time > 0)):
            vehicle.setColor(CF.Control["SpotTransColor"][0],CF.Control["SpotTransColor"][1],CF.Control["SpotTransColor"][2])
    else :
        vehicle.setColor(CF.Control["DefaultColor"][0],CF.Control["DefaultColor"][1],CF.Control["DefaultColor"][2]) #Change color to white

#----------------------------------------------------------------------

def tca_v(inputf = 'TCAinput.xml'):

    global timeval
    global vissimtimeit
    global changecolor

    program_st = time.time()

    vissimtimeit = False #True: time VISSIM without the TCA running.

    try:

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

        LastTP = 0
        headerBSM = True
        headerCAM = True 

        if len(sys.argv) == 2:
            inputf = sys.argv[1]
        CF = ControlFiles(inputf, TCA_version = 'vissim')
        CF.Load_files()

        if CF.Error_count() > 0:
            logging.critical("Errors in the control and/or strategy file, see TCA_Input_Summary.csv file for details")
            sys.exit()

        changecolor = CF.Control['ColorDisplay']

        RandomGen = Random_generator(CF.Control['Seed'])

        CF.Control['AccelColumn'] = True

        if CF.Control['RegionsFile'] is not None:
            unit_conversion = 100 / 2.54 / 12
            Regions = Load_Regions(CF.Control['RegionsFile'],CF.Control['Seed'],unit_conversion)
            print "Loading Regions File %s" % CF.Control['RegionsFile']
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

        RandomGen.add_generator_int('GapDistance', CF.Strategy["GapMinDistance"], CF.Strategy["GapMaxDistance"])
        RandomGen.add_generator_int('GapTimeout', CF.Strategy["GapMinTime"], CF.Strategy["GapMaxTime"])
        RandomGen.add_generator_int('psn', 0, 32767)  #range based on J2735
        RandomGen.add_generator_int('LossPercent', 1, 100)
        RandomGen.add_generator_int('TypePercent', 1, 100)

        output_file = TCA_Output(CF, Regions)

        Algorithm = TCA_Algorithm(CF, RSEs, RSE_Tree, RandomGen, Regions, SPOT_Tree)

        app = C2X_tca(CF.Control["OutputLevel"])

        app.run()

        if len(Algorithm.BSMs) > 0 :
            df_BSMs = pd.DataFrame(Algorithm.BSMs)
            df_BSMs = df_BSMs.sort(['transtime', 'Vehicle_ID'])
            df_BSMs = df_BSMs.drop('Vehicle_ID', axis = 1)
            df_BSMs['avg_accel'] = df_BSMs['avg_accel'].fillna(-9999.00)
            df_BSMs['heading'] = df_BSMs['heading'].fillna(-9999.00)
            df_BSMs['avg_accel'] = df_BSMs['avg_accel'].map(lambda x: '%.3f' % x) 
            df_BSMs['instant_accel'] = df_BSMs['instant_accel'].map(lambda x: '%.3f' % x) 
            df_BSMs['spd'] = df_BSMs['spd'].map(lambda x: '%.3f' % x) 
            df_BSMs['heading'] = df_BSMs['heading'].map(lambda x: '%.3f' % x) 
            df_BSMs.to_csv(path_or_buf =CF.Control["BSMTransFile"],
                           index=False,
                           mode='a',
                           header = headerBSM,
                           )

        if len(Algorithm.PDMs) > 0 :
            for ID in Algorithm.PDMBuffer.ActiveBuffers.keys():
                Algorithm.PDMBuffer.ClearBuffer(vehicleID = ID, locT = LastTP + 2, Snapshots = Algorithm.PDMs, reason = 2, transmitted_to = -1, transTime = -1)
            output_file.WriteSSList(Algorithm.PDMs, CF)

        if len(Algorithm.CAMs) > 0 :
            col = ['protocolVersion','messageID','stationID','generationDeltaTime','stationType','latitude',
               'longitude','semiMajorConfidence','semiMinorConfidence','altitudeValue','heading','headingConfidence',
               'speed','speedConfidence','driveDirection','longitudinalAcceleration','curvatureValue','curvatureConfidence',
               'yawRateValue','yawRateConfidence','vehicleLengthValue','vehicleLengthConfidence','vehicleWidth']
            df_CAMs = pd.DataFrame(Algorithm.CAMs, columns=col)
            df_CAMs['speed'] = df_CAMs['speed'].map(lambda x: '%.3f' % x) 
            df_CAMs['yawRateValue'] = df_CAMs['yawRateValue'].fillna(32767)
            df_CAMs['heading'] = df_CAMs['heading'].fillna(360)
            df_CAMs = df_CAMs.sort(['generationDeltaTime'])
            df_CAMs.to_csv(path_or_buf =CF.Control["CAMTransFile"], index=False,  mode='a', header = headerCAM)

        if len(Algorithm.TravelSPOTmsgs) > 0:
            output_file.WriteSPOTList(Algorithm.TravelSPOTmsgs, Algorithm.BehaviorSPOTmsgs, CF)


        Algorithm.tbl.list_veh_counts()

        if CF.Control["OutputLevel"] > 0:
            end_time = time.time()
            logger.info("End time %s (%f)" % (time.strftime('%X', time.localtime(end_time)), (end_time - program_st) ))
            logger.info("************  End Program  *******************")

        del Algorithm

    except BaseException, e:
        print str (e)
        raise
        time.sleep(4000)
    except:
        time.sleep(4000)


#----------------------------------------------------------------------


if __name__ == "__main__":
    tca_v()