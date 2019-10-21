
TCA 2.3 Overview
============================
The Trajectory Conversion Algorithm (TCA) Software is designed to test different strategies for producing, transmitting, and storing Connected Vehicle information. The TCA reads in and uses vehicle trajectory information or Vissim output, roadside equipment (RSE) location information, cellular or event region information and strategy information to produce a series of snapshots that a connected vehicle would produce. Vehicles can be equipped to generate and transmit Probe Data Messages (PDMs), Basic Safety Messages (BSMs), Cooperative Awareness Messages (CAMs) or ITS SPOT messages which can be transmitted by Dedicated Short Range Communication (DSRC) and/or via cellular. The TCA program version 2 build 3 or 2.3 includes simulated communication disruptions between vehicles and roadside equipment. As soon as a vehicle equipped to transmit via DSRC is in range of a RSE, it will download all of its snapshot information directly with a probabilistic uncertainty of the data being lost. Similarly, if the vehicle is equipped to transmit via cellular, it will download all its snapshot information directly but those snapshots might be lost or delayed due to user-defined loss rate and latency. In TCA 2.3, BSMs and PDMs can also be made to transmit at user-defined intervals.

Release Notes
-------------------
Release version 2.3

Support for international message types, the European Cooperative Awareness Message (CAM) and the Japanese ITS Spot message, has been added. CAM and ITS Spot both transmit via Dedicated Short Range Communication (DSRC) and produce message outputs consistent with publicly defined standards. Unlike previous versions of the TCA, TCA version 2.3 does not assume perfect communication between vehicles and roadside equipment and instead emulates the probabilistic uncertainties of DSRC. TCA version 2.3 also allows Probe Data Messages and Basic Safety Messages to be transmitted at user defined intervals. 

Release version 2.3.1
Added additional J2735 elements to the BSM output including DSRC Message ID and a temporary ID that changes every 5 minutes. Fixed a bug with the PDM Stop Snapshots. Improved the runtime and code efficiency. 


Release version 2.3.2
Fixed a bug in equipping vehicles via their Vehicle IDs. Fixed a bug in reading a vehicle trajectory file with non-sequential vehicle ID numbers.

License information
-------------------
Licensed under the Apache License, Version 2.0 (the "License"); you may not use this
file except in compliance with the License.
You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under
the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. See the License for the specific language governing
permissions and limitations under the License.

System Requirements
-------------------------
The TCA 2.0 software can run on most standard Window or Linux based computers with 
Pentium core processers, with at least two gigabits of RAM and at least 100 MB of drive space.
Performance of the software will be based on the computing power and available RAM in 
the system.  Larger datasets can require much larger space requirements depending on the 
amount of data being read into the software.

The TCA 2.0 software application was developed using the open source
programming language Python 2.7 (www.python.org).  The application requires Python 2.7
or higher to run.  Note that Python 3.0 is a change from Python 2.X language and will not
run the DMA performance measurement application.  Python versions 2.7.X – 2.9.X will work.

The application can be run on Windows, Linux, or Mac operating systems.  Python is installed
by default on many Linux and Mac operating systems.


Documentation
-------------
The TCA 2.0 software is packaged with Word based User Guide
"The Trajectory Convertor Algorithm 2 3 User manual.doc" that contains all information about background
purpose, benefits, objectives, inputs/outputs, how to run the software and requirements for the software.


Support Contact
------------------------------------
Jim Larkin and James O'HAra from Noblis

Code.gov Info
----------------
Agency: DOT

Short Description: The The Trajectory Conversion Algorithm (TCA) reads in and uses vehicle trajectory information or Vissim output, roadside equipment (RSE) location information, cellular or event region information and strategy information to produce a series of snapshots that a connected vehicle would produce.

Status: Beta

Tags: transporation, connected vehicles, cost planning

Labor Hours: 0

Contact Name: James O'Hara

Contact Phone: 703-610-1632
