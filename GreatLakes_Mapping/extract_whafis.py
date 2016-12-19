#!/usr/bin/env python
""" Get WHAFIS data from files programatically.
Python=3
Author: J. Dorvinen
Date: 12/16/2016
Email: jdorvinen@dewberry.com """
# Import required modules
import re
import os
DIRECT = os.path.dirname(__file__)
os.chdir(DIRECT)

# Count out, or OUT files
OUTS_SML = len([f for f in os.listdir('.') if os.path.isfile(f) and f.startswith('w') and f.endswith('.out')])
OUTS_BIG = len([f for f in os.listdir('.') if os.path.isfile(f) and f.startswith('W') and f.endswith('.OUT')])

if OUTS_SML > 0:
    TRANSECT_COUNT = OUTS_SML
    WFILE = 'w{}.out'
elif OUTS_BIG > 0:
    TRANSECT_COUNT = OUTS_BIG
    WFILE = 'W{}.OUT'
else:
    print("Error: no '.out' files found")

# Define outfile location
OUTFILE = os.path.join(DIRECT, "WHAFIS.csv")

# Define helper functions
def find_station(i, wave_height=1.5):
    """ Find station for given wave height from WHAFIS output, defaults to LiMWA """
    filename = os.path.join(DIRECT, WFILE.format(i))
    with open(filename, 'r') as whafis:
        wave_ht = [0, 0]
        wave_st = [0, 0]
        station = 0
        elevation = 0
        for line in whafis:
            if re.search(r"WAVE HEIGHT  WAVE PERIOD     ELEVATION", line):
                whafis.readline()
                dataline = whafis.readline().strip().split()
                wave_ht[0] = float(dataline[2])
                wave_st[0] = float(dataline[1])
                if wave_ht[0] < wave_height:
                    elevation = -999
                    station = -999
                elif wave_ht[0] == wave_height:
                    station = wave_st[0]
                else:
                    while station == 0:
                        whafis.readline()
                        dataline = whafis.readline().strip().split()
                        wave_ht[1] = float(dataline[2])
                        wave_st[1] = float(dataline[1])
                        if wave_ht[1] == wave_height:
                            station = wave_st[1]
                        elif wave_ht[1] < wave_height:
                            station = wave_st[0] +\
                                      ((wave_st[1]-wave_st[0])/(wave_ht[1]-wave_ht[0])) *\
                                      (wave_height-wave_ht[0])
                            station = ((station*100)//1)/100
                        else:
                            wave_ht[0] = wave_ht[1]
                            wave_st[0] = wave_st[1]
    return station, elevation

def find_elevation(i, station):
    """ Find ground surface elevation from WHAFIS input for a given station """
    filename = os.path.join(DIRECT, WFILE.format(i))
    with open(filename, 'r') as whafis:
        stations = [0, 0]
        elevations = [0, 0]
        elevation = 0
        for line in whafis:
            if re.search(r"PART1 INPUT", line):
                whafis.readline()
                dataline = whafis.readline().strip().split()
                stations[0] = float(dataline[1])
                elevations[0] = float(dataline[2])
                if stations[0] == station:
                    elevation = elevations[0]
                else:
                    while elevation == 0:
                        dataline = whafis.readline().strip().split()
                        stations[1] = float(dataline[1])
                        elevations[1] = float(dataline[2])
                        if stations[1] == station:
                            elevation = elevations[1]
                        elif stations[1] > station:
                            elevation = elevations[0] +\
                                        ((elevations[1]-elevations[0])/(stations[1]-stations[0])) *\
                                        (station-stations[0])
                            elevation = ((elevation*100)//1)/100
                        else:
                            stations[0] = stations[1]
                            elevations[0] = elevations[1]
    return elevation

# Define Main function
def main(outfile):
    """ main function """
    with open(outfile, 'w') as out:
        out.write("  TRANSECT, WHAFIS_ZN, WHAFIS_EL, WHAFIS_WH,  LIMWA_ST,  LIMWA_EL,     VA_ST,     VA_EL\n")
        for i in range(1, TRANSECT_COUNT+1):
            filename = os.path.join(DIRECT, WFILE.format(i))
            with open(filename, 'r') as whafis:
                for line in whafis:
                    # Find controlling wave height
                    if re.search(r"WAVE HEIGHT  WAVE PERIOD     ELEVATION", line):
                        whafis.readline()
                        whafis_wh = whafis.readline().strip().split()[2]
                    elif re.search(r"STATION OF GUTTER  ELEVATION  ZONE DESIGNATION   FHF", line):
                        whafis.readline()
                        whafis.readline()
                        # WHAFIS water elevation
                        whafis_el = whafis.readline().strip().rsplit()[1]
                        whafis.readline()
                        # WHAFIS zone (AE or VE)
                        whafis_zn = whafis.readline().strip().split()[0]+"E"

            # Find location of LiMWA
            limwa_st, limwa_el = find_station(i, wave_height=1.5)
            if limwa_el == 0:
                limwa_el = find_elevation(i, station=limwa_st)

            # Find location of VA transition (This could be taken from WHAFIS output part 5)
            va_st, va_el = find_station(i, wave_height=3)
            if va_el == 0:
                va_el = find_elevation(i, station=va_st)

            # Write WHAFIS data to output file
            outtext = "{0:>10},{1:>10},{2:>10},{3:>10},{4:>10.2f},{5:>10.2f},{6:>10.2f},{7:>10.2f}\n"
            outline = outtext.format(i,
                                     whafis_zn,
                                     whafis_el,
                                     whafis_wh,
                                     limwa_st,
                                     limwa_el,
                                     va_st,
                                     va_el)
            out.write(outline)

if __name__ == '__main__':
    main(outfile=OUTFILE)
