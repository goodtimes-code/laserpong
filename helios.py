"""
Helios DAC
Python lib incl. basic shapes

2022-11-18, Oliver Baltz

TODOs:
    * Solve flickering when having multiple circles on screen (by implementing quuee? by calling draw_circle async?)

"""

import ctypes
import sys
import os

SCAN_RATE = 40000 #kbps

# define point structure
class HeliosPoint(ctypes.Structure):
    #_pack_=1
    _fields_ = [('x', ctypes.c_uint16),
                ('y', ctypes.c_uint16),
                ('r', ctypes.c_uint8),
                ('g', ctypes.c_uint8),
                ('b', ctypes.c_uint8),
                ('i', ctypes.c_uint8)] # useless


def initialize():
    global HeliosLib
    HeliosLib = ctypes.cdll.LoadLibrary("./libHeliosDacAPI.so")
    numDevices = HeliosLib.OpenDevices()
    print("Found ", numDevices, "Helios DACs")


def draw_point(x=0, y=0, r=0, g=0, b=40, i=0):
    frameType = HeliosPoint * 1

    wait_until_ready()

    blankPoint = frameType()
    blankPoint = HeliosPoint(int(x),int(y), 0, 0, 0, 0)
    HeliosLib.WriteFrame(0, SCAN_RATE, 0, ctypes.pointer(blankPoint), 1) # blank

    wait_until_ready()

    #int HeliosDac::WriteFrame(unsigned int devNum, unsigned int pps, std::uint8_t flags, HeliosPoint* points, unsigned int numOfPoints)
    pointFrame = frameType()
    pointFrame = HeliosPoint(int(x),int(y),r,g,b,i)
    HeliosLib.WriteFrame(0, SCAN_RATE, 0, ctypes.pointer(pointFrame), 1)


def draw_line(from_x, from_y, to_x, to_y, r, g, b):

    #print('[HELIOS] Draw line from: (' + str(from_x) + ',' + str(from_y) + ') to ('+str(to_x)+','+str(to_y)+')')

    # generated vertices
    point_type = HeliosPoint * 2
    points = point_type()

    wait_until_ready()

    points[0] = HeliosPoint(int(from_x), int(from_y), r, g, b, 0)
    points[1] = HeliosPoint(int(to_x), int(to_y), r, g, b, 0)

    # draw points
    HeliosLib.WriteFrame(0, 1000, 0, ctypes.pointer(points), 2)


def draw_circle(center_x, center_y, radius, r, g, b):
    import math

    # the lower this value the higher quality the circle is with more points generated
    step_size = 0.1

    # generated vertices
    points_count = int(2 * math.pi / step_size) + 1
    point_type = HeliosPoint * points_count
    points = point_type()

    # calculate points
    t = 0
    i = 0
    first_x = int(round(radius * math.cos(0) + center_x, 0))
    first_y = int(round(radius * math.sin(0) + center_y, 0))
    while t < 2 * math.pi:
        points[i] = HeliosPoint(int(round(radius * math.cos(t) + center_x, 0)), int(round(radius * math.sin(t) + center_y, 0)), r, g, b, 0)
        t += step_size
        i += 1

    wait_until_ready()

    draw_point(first_x, first_y, 0, 0, 0, 0) # blank

    wait_until_ready()

    # draw points
    HeliosLib.WriteFrame(0, SCAN_RATE, 0, ctypes.pointer(points), points_count)


def wait_until_ready():
    # make some attempts for DAC status to be ready. After that, just give up and try to write the frame anyway
    statusAttempts = 0
    max_status_attempts = 512
    while (statusAttempts < max_status_attempts and HeliosLib.GetStatus(0) != 1):
            statusAttempts += 1


def close():
    print('Closing device connection...')
    HeliosLib.CloseDevices()
    print('Connection closed.')


def main():
    initialize()

    while True:
        draw_line(2000, 1500, 2000, 2500, 0, 0, 80)
        #draw_circle(2000, 2500, 60, 0, 0, 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            close()
            sys.exit(0)
        except SystemExit:
            os._exit(0)
