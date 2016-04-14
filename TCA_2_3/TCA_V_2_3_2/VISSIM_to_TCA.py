import pandas as pd
import sys

#Check for control file
if len(sys.argv) == 2:
    inputf = sys.argv[1]
else:
    print "Add name of file after program"
    print 'python VISSIM_to_TCA <<file to convert>>'
    sys.exit(0)


line_skip = 0
with open(inputf) as in_f:
    line = in_f.readline()
    while 'VehNr;' not in line:
        line = in_f.readline()
        line_skip += 1

df = pd.read_csv(inputf, sep=';', skipinitialspace=True, header=1, skiprows=(line_skip-1))

if ('VehNr' in df.columns):
    print "Loading %s vehicles" % str(len(df['VehNr'].unique()))


if ('VehNr' in df.columns) and ('t' in df.columns) and ('WorldX' in df.columns) and \
   ('WorldY' in df.columns) and ('v' in df.columns):

    df = df[['VehNr', 't', 'WorldX', 'WorldY', 'v']] #cut out unneeded columns

    df = df[(df['t'] % 1 == 0)] #remove 1/10 Second values

    f_st, f_end =  inputf.split('.')

    newfile = f_st + '_tca.csv'

    df.to_csv(newfile, index=False)

else:
    print 'Error: VISSIM fzp file does not have all required fields of: VehNr, t, WorldX, WorldY, and v'