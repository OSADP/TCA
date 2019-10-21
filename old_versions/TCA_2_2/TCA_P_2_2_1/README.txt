
TCA-P 2.2 Overview
============================
The Trajectory Converter Analysis-PARAMICS (TCA-P) Software is designed to test different strategies for producing, transmitting, and storing Connected Vehicle information. The TCA-P runs with the PARAMICS tool using real-time simulation vehicle information, Roadside Equipment (RSE) location information, cellular or event region information, and strategy information to produce a series of snapshots that the vehicle would produce. Vehicles can be equipped to generate and transmit Probe Data Messages (PDMs) and/or Basic Safety Messages (BSMs) which can be transmitted by Dedicated Short Range Communication (DSRC) and/or via cellular. The TCA program version 2 Build 2 or 2.2 assumes perfect communication between vehicles and RSEs but future versions of the TCA 2 will include simulated communication disruptions. As soon as a vehicle equipped to transmit via DSRC is in range of a RSE, it will download all of its snapshot information directly without any loss of information. Similarly, if the vehicle is equipped to transmit via cellular, it will download all its snapshot information directly but those snapshots might be lost or delayed due to user-defined loss rate and latency.

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
"The Trajectory Convertor Analysis-PARAMICS 2.2 User manual.doc" that contains all information about background
purpose, benefits, objectives, and requirements for the software.

Web sites
---------
The TCA 2.0 software is distributed through the USDOT's JPO
Open Source Application Development Portal (OSADP)

http://itsforge.net/ 
