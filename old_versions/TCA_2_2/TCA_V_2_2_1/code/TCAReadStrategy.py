#Standard
import xml.etree.ElementTree as ET
import unittest


#-----------------------------------------------------------------------
def ReadStrategyFile(CV):    
    
    if CV.Debugger >= 1:
        print "Reading Strategy File %s" % (CV.Control["strategy"])

    tree = ET.parse(CV.Control["strategy"])
    root = tree.getroot()

    errors = []

    #Load Title
    try:
        CV.Strategy["title"] = root.find("Title").text
    except:
        errors.append("Error: No Title Tag found in Strategy file %s" % CV.Control["strategy"])

    #Load DSRC Information
    #--------------------------------------------------------------
    if root.find("Inputs/DSRC") != None:

      #Load PSN Strategy information
      #--------------------------------------------------------------
      try:
          CV.Strategy["TimeBetweenPSNSwitches"] = int(root.find("Inputs/DSRC/PSNStrategy/TimeBetweenPSNSwitches").text)
      except:
          errors.append("Error: No TimeBetweenPSNSwitches Tag found or not a integer in control file %s" % CV.Control["strategy"])

      try:
          CV.Strategy["DistanceBetweenPSNSwitches"] = int(root.find("Inputs/DSRC/PSNStrategy/DistanceBetweenPSNSwitches").text)
      except:
          errors.append("Error: No TimeBetweenPSNSwitches Tag found or not a integer in control file %s" % CV.Control["strategy"])

      try:
          CV.Strategy["RSEFlag"] = int(root.find("Inputs/DSRC/PSNStrategy/RSEFlag").text)
      except:
          errors.append("Error: No TimeBetweenPSNSwitches Tag found or not a integer in control file %s" % CV.Control["strategy"])

      try:
          CV.Strategy["Gap"] = int(root.find("Inputs/DSRC/PSNStrategy/Gap").text)
      except:
          errors.append("Error: No TimeBetweenPSNSwitches Tag found or not a integer in control file %s" % CV.Control["strategy"])


      #Load StopStart Strategy information
      #--------------------------------------------------------------
      if CV.Debugger >= 2:
          print "Reading Stop Start Strategy"

      try:
          CV.Strategy["StopStartStrategy"] = int(root.find("Inputs/DSRC/StopStartStrategy/Strategy").text)
      except:
          errors.append("Error: No StopStartStrategy/Strategy Tag found or not a integer in control file %s" % CV.Control["strategy"])

      try:
          CV.Strategy["StopThreshold"] = int(root.find("Inputs/DSRC/StopStartStrategy/StopThreshold").text)
      except:
          errors.append("Error: No StopThreshold Tag found or not a integer in control file %s" % CV.Control["strategy"])

      try:
          CV.Strategy["StopLag"] = int(root.find("Inputs/DSRC/StopStartStrategy/StopLag").text)
      except:
          errors.append("Error: No Inputs/StopStartStrategy/StopLag Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      try:
          CV.Strategy["StartThreshold"] = int(root.find("Inputs/DSRC/StopStartStrategy/StartThreshold").text)
      except:
          errors.append("Error: No Inputs/StopStartStrategy/StartThreshold Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      try:
          CV.Strategy["MultipleStops"] = int(root.find("Inputs/DSRC/StopStartStrategy/MultipleStops").text)
      except:
          errors.append("Error: No Inputs/StopStartStrategy/MultipleStops Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      #Load Periodic Strategy information
      #--------------------------------------------------------------
      if CV.Debugger >= 2:
          print "Reading Periodic Strategy"

      try:
          CV.Strategy["PeriodicStrategy"] = int(root.find("Inputs/DSRC/PeriodicStrategy/Strategy").text)
      except:
          errors.append("Error: No Inputs/PeriodicStrategy/Strategy Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      try:
          CV.Strategy["LowSpeedThreshold"] = int(root.find("Inputs/DSRC/PeriodicStrategy/LowSpeedThreshold").text)
      except:
          errors.append(
              "Error: No Inputs/PeriodicStrategy/LowSpeedThreshold Tag found or not a integer in control file %s"
              % CV.Control["strategy"])

      try:
          CV.Strategy["ShortSpeedinterval"] = int(root.find("Inputs/DSRC/PeriodicStrategy/ShortSpeedinterval").text)
      except:
          errors.append(
              "Error: No Inputs/PeriodicStrategy/ShortSpeedinterval Tag found or not a integer in control file %s"
              % CV.Control["strategy"])

      try:
          CV.Strategy["HighSpeedThreshold"] = int(root.find("Inputs/DSRC/PeriodicStrategy/HighSpeedThreshold").text)
      except:
          errors.append(
              "Error: No Inputs/PeriodicStrategy/HighSpeedThreshold Tag found or not a integer in control file %s"
              % CV.Control["strategy"])

      try:
          CV.Strategy["LongSpeedinterval"] = int(root.find("Inputs/DSRC/PeriodicStrategy/LongSpeedinterval").text)
      except:
          errors.append(
              "Error: No Inputs/PeriodicStrategy/LongSpeedinterval Tag found or not a integer in control file %s"
              % CV.Control["strategy"])

      try:
          CV.Strategy["MaxDeltaSpeed"] = float(root.find("Inputs/DSRC/PeriodicStrategy/MaxDeltaSpeed").text)
      except:
          errors.append("Error: No Inputs/PeriodicStrategy/MaxDeltaSpeed Tag found or not a float in control file %s"
                        % CV.Control["strategy"])


      #Load Buffer Strategy information
      #--------------------------------------------------------------
      if CV.Debugger >= 2:
          print "Reading Buffer Strategy"

      try:
          CV.Strategy["TotalCapacity"] = int(root.find("Inputs/DSRC/BufferStrategy/TotalCapacity").text)
      except:
          errors.append("Error: No Inputs/BufferStrategy/TotalCapacity Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      try:
          CV.Strategy["SSRetention"] = int(root.find("Inputs/DSRC/BufferStrategy/SSRetention").text)
      except:
          errors.append("Error: No Inputs/BufferStrategy/SSRetention Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      #Load RSE information
      #--------------------------------------------------------------
      if CV.Debugger >= 2:
          print "Reading RSE Information"

      try:
          CV.Strategy["MinRSERange"] = int(root.find("Inputs/DSRC/RSEInformation/MinRSERange").text)
      except:
          errors.append("Error: No Inputs/RSEInformation/MinRSERange Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])
      try:
          CV.Strategy["MaxRSERange"] = int(root.find("Inputs/DSRC/RSEInformation/MaxRSERange").text)
      except:
          errors.append("Error: No Inputs/RSEInformation/MaxRSERange Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      try:
          CV.Strategy["TimeoutRSE"] = int(root.find("Inputs/DSRC/RSEInformation/TimeoutRSE").text)
      except:
          errors.append("Error: No Inputs/RSEInformation/TimeoutRSE Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      try:
          CV.Strategy["MinNumberofSStoTransmit"] = int(root.find("Inputs/DSRC/RSEInformation/MinNumberofSStoTransmit").text)
      except:
          errors.append(
              "Error: No Inputs/RSEInformation/MinNumberofSStoTransmit Tag found or not a integer in control file %s"
              % CV.Control["strategy"])

      try:
          CV.Strategy["RSEReports"] = int(root.find("Inputs/DSRC/RSEInformation/RSEReports").text)
      except:
          errors.append("Error: No Inputs/RSEInformation/RSEReports Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      #Load Gap information
      #--------------------------------------------------------------
      if CV.Debugger >= 2:
          print "Reading Gap Information"

      try:
          CV.Strategy["GapMinTime"] = int(root.find("Inputs/DSRC/GapInformation/MinTime").text)
      except:
          errors.append("Error: No Inputs/GapInformation/MinTime Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      try:
          CV.Strategy["GapMaxTime"] = int(root.find("Inputs/DSRC/GapInformation/MaxTime").text)
      except:
          errors.append("Error: No Inputs/GapInformation/MaxTime Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      try:
          CV.Strategy["GapMinDistance"] = int(root.find("Inputs/DSRC/GapInformation/MinDistance").text)
      except:
          errors.append("Error: No Inputs/GapInformation/MinDistance Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      try:
          CV.Strategy["GapMaxDistance"] = int(root.find("Inputs/DSRC/GapInformation/MaxDistance").text)
      except:
          errors.append("Error: No Inputs/GapInformation/MaxDistance Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

    #Load Cellular information
    #--------------------------------------------------------------
    if root.find('Inputs/Cellular') != None:
      if CV.Debugger >= 2:
          print "Reading Cellular Information"

      try:
          CV.Strategy["CellularFlag"] = int(root.find("Inputs/Cellular/CellularFlag").text)
      except:
          errors.append("Error: No Inputs/Cellular/Cellular Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])
          
      try:
          CV.Strategy["MinNumberofSStoTransmitViaCellular"] = int(root.find("Inputs/Cellular/MinNumberofSStoTransmitViaCellular").text)
      except:
          errors.append("Error: No Inputs/Cellular/MinNumberofSStoTransmitViaCellular Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

      try:
        CV.Strategy["DefaultLossPercent"] = int(root.find('Inputs/Cellular/DefaultLossPercent').text)
      except:
          errors.append( "Error: No DefaultLossPercent Tag found in strategy file %s"  % CV.Control["strategy"])
      try:
          CV.Strategy["DefaultLatency"] = float(root.find('Inputs/Cellular/DefaultLatency').text) / 1000
      except:
          errors.append( "Error: No DefaultLatency Tag found in strategy file %s"  % CV.Control["strategy"])

      #Loop through each region and add cellular regions to a list of dictionaries
      keys = ['X1','Y1','X2','Y2','LossPercent','Latency','Name']
      region_list = []
      for i in range(1,8):
        region = 'Region' + str(i)
        if root.find('Inputs/Cellular/%s' % region) != None: #Region is not defined
          try:
            values = map(int, (root.find('Inputs/Cellular/%s/Point1' % region).text).split(','))
            values.extend(map(int, (root.find('Inputs/Cellular/%s/Point2' % region).text).split(',')))
            values.append(int(root.find('Inputs/Cellular/%s/LossPercent' % region).text))
            values.append((float(root.find('Inputs/Cellular/%s/Latency' % region).text)) / 1000)
            values.append(root.find('Inputs/Cellular/%s/Name' % region).text)
            region_list.append(dict(zip(keys,values)))
          except:
            errors.append( "Error: Missing Cellular Tag in strategy file %s for region %s"  % (CV.Control["strategy"],region))
      CV.Strategy["Regions"] = region_list
    else:
      CV.Strategy["CellularFlag"] = False

    if root.find('Inputs/BSMFlag') != None:
      try:
          CV.Strategy["BSMFlag"] = int(root.find("Inputs/BSMFlag").text)
      except:
          errors.append("Error: No Inputs/BSMFlag Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])

    if root.find('Inputs/BSMdebugFlag') != None:
      try:
          CV.Strategy["BSMdebugFlag"] = int(root.find("Inputs/BSMdebugFlag").text)
      except:
          errors.append("Error: No Inputs/BSMdebugFlag Tag found or not a integer in control file %s"
                        % CV.Control["strategy"])
    else:
        CV.Strategy['BSMdebugFlag'] = 0

    if CV.Debugger >= 3:
        for key, value in CV.Control.iteritems():
            print "%s: %s" % (key, value)

    return errors


#*************************************************************************
class LoadStrategyTest(unittest.TestCase):

    def setUp(self):

        from TCALoadControl import ControlFiles

        self.CF = ControlFiles()
        self.CF.map_dictionary()
        self.CF.Control['OutputLevel'] = 0
        self.CF.Control['StrategyFile'] = 'tca_delete_me_test_file_good.xml'

        with open('tca_delete_me_test_file_good.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
                    <Strategy>
                      <Title>J2735 Noblis Modified Strategy</Title>
                    <Inputs>
                     <DSRC>
                     <PSNStrategy>
                      <TimeBetweenPSNSwitches>120</TimeBetweenPSNSwitches>
                      <DistanceBetweenPSNSwitches>3281</DistanceBetweenPSNSwitches>
                      <Gap>0</Gap>
                      </PSNStrategy>
                     <StopStartStrategy>
                      <StrategyID>1</StrategyID>
                      <StopThreshold>5</StopThreshold>
                      <StopLag>15</StopLag>
                      <StartThreshold>10</StartThreshold>
                      <MultipleStops>0</MultipleStops>
                      </StopStartStrategy>
                     <PeriodicStrategy>
                      <StrategyID>1</StrategyID>
                      <LowSpeedThreshold>20</LowSpeedThreshold>
                      <ShortSpeedinterval>6</ShortSpeedinterval>
                      <HighSpeedThreshold>60</HighSpeedThreshold>
                      <LongSpeedinterval>20</LongSpeedinterval>
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
                      </RSEInformation>
                     <GapInformation>
                      <MinTime>3</MinTime>
                      <MaxTime>13</MaxTime>
                      <MinDistance>164</MinDistance>
                      <MaxDistance>820</MaxDistance>
                      </GapInformation>
                      </DSRC>
                      </Inputs>
                      </Strategy>""")

        with open('tca_delete_me_test_file_bad.xml', 'wb') as f_out:
            f_out.write("""<?xml version="1.0" encoding="UTF-8" ?>
                        <Strategy>
                          <Title>J2735 Noblis Modified Strategy</Title>
                        <Inputs>
                        <DSRC>
                         <PSNStrategy>
                          <TimeBetweenPSNSwitches>120</TimeBetweenPSNSwitches>
                          <DistanceBetweenPSNSwitches>3281</DistanceBetweenPSNSwitches>
                          <Gap>0</Gap>
                          </PSNStrategy>
                         <StopStartStrategy>
                          <StrategyID>1</StrategyID>
                          <StopThreshold>5</StopThreshold>
                          <StopLag>15</StopLag>
                          <StartThreshold>10</StartThreshold>
                          </StopStartStrategy>
                         <PeriodicStrategy>
                          <StrategyID>1</StrategyID>
                          <LowSpeedThreshold>20</LowSpeedThreshold>
                          <ShortSpeedinterval>A</ShortSpeedinterval>
                          <HighSpeedThreshold>60</HighSpeedThreshold>
                          <LongSpeedinterval>20</LongSpeedinterval>
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
                          </Inputs>
                          </Strategy>""")

    def test_load(self):
        self.CF.Control['strategy'] = 'tca_delete_me_test_file_good.xml'
        errors = ReadStrategyFile(self.CF)
        assert len(errors) ==0
        assert self.CF.Strategy["RSEFlag"] == 0
        assert self.CF.Strategy["StartThreshold"] == 10
        assert self.CF.Strategy["DistanceBetweenPSNSwitches"] == 3281

    def test_load_bad(self):
        self.CF.Control['strategy'] = 'tca_delete_me_test_file_bad.xml'
        errors = ReadStrategyFile(self.CF)
        assert len(errors) == 3


    def tearDown(self):
        import os
        os.remove('tca_delete_me_test_file_good.xml')
        os.remove('tca_delete_me_test_file_bad.xml')


if __name__ == '__main__':
  pass
    #unittest.main()