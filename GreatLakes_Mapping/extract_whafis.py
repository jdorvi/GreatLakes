#!/usr/bin/env python
""" Get WHAFIS data from files programatically, runs in current directory.
Python=2 or 3
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
def find_elevation(filename, station):
    """ Find ground surface elevation from WHAFIS input for a given station """
    with open(filename, 'r') as whafis:
        stations = [0, 0]
        elevations = [0, 0]
        elevation = -999
        for line in whafis:
            if re.search(r"PART1 INPUT", line):
                whafis.next()
                dataline = whafis.next().strip().split()
                stations[0] = float(dataline[1])
                elevations[0] = float(dataline[2])
                if stations[0] == station:
                    elevation = elevations[0]
                else:
                    while elevation == -999:
                        dataline = whafis.next().strip().split()
                        stations[1] = float(dataline[1])
                        elevations[1] = float(dataline[2])
                        if stations[1] == station:
                            elevation = elevations[1]
                        elif stations[1] > station:
                            elevation = elevations[0] +\
                                        (station-stations[0]) *\
                                        ((elevations[1]-elevations[0])/(stations[1]-stations[0]))
                            elevation = ((elevation*100)//1)/100
                        else:
                            stations[0] = stations[1]
                            elevations[0] = elevations[1]
    return elevation

def find_limwa_gutter(filename, wave_height=1.5):
    """ Find station for given wave height from WHAFIS output, defaults to LiMWA """
    with open(filename, 'r') as whafis:
        wave_ht = [0, 0] # Y
        wave_st = [0, 0] # X
        wave_sw = [0, 0]
        station, elevation, swel = -999, -999, -999
        for line in whafis:
            if re.search(r"PART2: CONTROLLING WAVE HEIGHTS, SPECTRAL", line):
                for i in range(5):
                    whafis.next()
                dataline = whafis.next().strip().split()
                wave_ht[0] = float(dataline[-3])
                wave_st[0] = float(dataline[-4])
                wave_sw[0] = float(dataline[-1])
                if wave_ht[0] < wave_height:
                    pass
                elif wave_ht[0] == wave_height:
                    station = wave_st[0]
                    swel = wave_sw[0]
                else:
                    while station == -999:
                        whafis.next()
                        dataline = whafis.next().strip().split()
                        wave_ht[1] = float(dataline[-3])
                        wave_st[1] = float(dataline[-4])
                        wave_sw[1] = float(dataline[-1])
                        if wave_ht[1] == wave_height:
                            station = wave_st[1]
                            swel = wave_sw[1]
                        elif wave_ht[1] < wave_height:
                            station = wave_st[0] +\
                                      (wave_ht[0] - wave_height) *\
                                      ((wave_st[1]-wave_st[0])/(wave_ht[0]-wave_ht[1]))
                            station = ((station*100)//1)/100
                            swel = wave_sw[0] +\
                                   (wave_ht[0] - wave_height) *\
                                   ((wave_sw[1]-wave_sw[0])/(wave_ht[0]-wave_ht[1]))
                            swel = ((swel*100)//1)/100
                        else:
                            wave_ht[0] = wave_ht[1]
                            wave_st[0] = wave_st[1]
    if station != -999:
        elevation = find_elevation(filename, station)
    return station, elevation, swel

def find_vzone_gutter(filename):
    """ Finds V Zone gutter based on Part 5 of WHAFIS output """
    station, elevation, swel = -999, -999, -999
    with open(filename, 'r') as whafis:
        for line in whafis:
            if re.search(r"PART5  LOCATION OF V ZONES", line):
                for i in range(3):
                    whafis.next()
                station = float(whafis.next().strip().split()[0]) # Station
            elif re.search(r"PART6 NUMBERED A ZONES AND V ZONES", line):
                if station != -999:
                    while swel == -999:
                        temp = whafis.next().strip().split()
                        if len(temp) == 2:
                            if float(temp[0]) == station:
                                swel = float(temp[1]) # Elevation
                            else:
                                for i in range(3):
                                    whafis.next()
    if station != -999:
        elevation = find_elevation(filename, station)
    return station, elevation, swel

def find_controlling_params(filename):
    """ Searches for and finds controlling parameters from WHAFIS output file """
    with open(filename, 'r') as whafis:
        for line in whafis:
            # Find controlling wave height
            if re.search(r"PART2: CONTROLLING WAVE HEIGHTS, SPECTRAL", line):
                for i in range(5):
                    whafis.next()
                whafis_wave = whafis.next().strip().split()[-3]
            elif re.search(r"PART6 NUMBERED A ZONES AND V ZONES", line):
                for i in range(4):
                    whafis.next()
                # WHAFIS water elevation
                whafis_swel = whafis.next().strip().rsplit()[1]
                whafis.next()
                # WHAFIS zone (AE or VE)
                whafis_zone = whafis.next().strip().split()[0]+"E"
    return whafis_zone, whafis_wave, whafis_swel


# Define Main function
def main(outfile):
    """ main function """
    with open(outfile, 'w') as out:
        out.write(" TRANSECT," +
                  " WHAFIS_ZONE, WHAFIS_WAVE, WHAFIS_SWEL," +
                  " LIMWA_STAT, LIMWA_ELEV, LIMWA_SWEL," +
                  " VA_STAT, VA_ELEV, VA_SWEL\n")
        for i in range(1, TRANSECT_COUNT+1):
            # Update filename
            filename = os.path.join(DIRECT, WFILE.format(i))

            # Find controlling WHAFIS parameters
            whafis_zone, whafis_wave, whafis_swel = find_controlling_params(filename)

            # Find location of LiMWA gutter
            limwa_stat, limwa_elev, limwa_swel = find_limwa_gutter(filename)

            # Find location of VA transition
            va_stat, va_elev, va_swel = find_vzone_gutter(filename)

            # Write WHAFIS data to output file
            outtext = "{0:>9},{1:>12},{2:>12},{3:>12}," +\
                      "{4:>11.2f},{5:>11.2f},{6:>11.2f}," +\
                      "{7:>8.2f},{8:>8.2f},{9:>8.2f}\n"
            outline = outtext.format(i,
                                     whafis_zone, whafis_wave, whafis_swel,
                                     limwa_stat, limwa_elev, limwa_swel,
                                     va_stat, va_elev, va_swel)
            out.write(outline)

if __name__ == '__main__':
    main(outfile=OUTFILE)
