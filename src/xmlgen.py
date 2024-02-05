#! /usr/bin/env python
""" 
 Generate the XML file from the YAML file.
 The yaml file has a 'config' entry. This in turn contains a list of entries
 that represent various groups of sensors. For each group, there is a list of
 sensors and possibly a list of devices. If there are devices, then
 the sensors are repeated for each device.
 """

from math import ceil
import xml.etree.ElementTree as ET
import argparse
import os
import pprint
import yaml

import utils # local import

def sensor_size(thedict: dict) -> int:
    """calculate the size of the sensor in bytes"""
    sz = 2 # default size
    if '32' in thedict['type']:
        sz = 4
    elif 'char' in thedict['type']:
        sz = 1*thedict['char_count'] # 1 for char type
    return sz

def type_to_format(thedict: dict) -> str:
    """calculate the format of the sensor"""
    if 'uint' in thedict['type']: # uint16, uint32, uint8
        fmt = "u"
    elif 'int' in thedict['type']: # int16, int32, int8
        fmt = "d"
    elif thedict['type'] == 'fp16':
        fmt = "fp16"
    elif thedict['type'] == 'char':
        fmt = "c"
    else:
        print("ERROR: unknown type", thedict['type'])
        return None
    return fmt


def make_node(parent: ET.Element, myid: str, thedict: dict, address: int) -> ET.Element:
    """create the node to be inserted into the xml tree"""
    thenode = ET.SubElement(parent, 'node')
    myid = myid.replace(' ', '_')
    thenode.set('id', myid)
    halfaddr = int(address/2)
    thenode.set('address', str(hex(halfaddr)))
    thenode.set("permission", "r")
    width = sensor_size(thedict)*8 # size in bits
    theformat = type_to_format(thedict) # format of the sensor
    thenode.set('format', theformat)

    # char type sensors are handled differently
    if thedict['type'] == 'char':
        thenode.set('mode', "incremental")
        val = int(ceil(thedict['char_count']/4.)) # 4 chars per 32 bit word here
        print(f"char_count: {thedict['char_count']}, val: {val}")
        thenode.set('size', str(hex(val)))
    else: # all other types have masks
        mask = (1 << width) - 1
        is_odd = address % 2 == 1
        if not is_odd :
            thenode.set('mask', "0x{0:08X}".format(mask))
        else:
            thenode.set('mask', "0x{0:08X}".format(mask << 16))
    if 'extra' in thedict:
        extra = thedict['extra']
        if not "Column" in extra:
            extra = extra + ";Column=" + myid
        if not "Row" in extra:
            extra = extra + ";Row=" + myid
        thenode.set('extra', extra)
    return thenode

def main():
    """main function"""
    parser = argparse.ArgumentParser(description='Process YAML for XML.')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='increase output verbosity')
    parser.add_argument('-d', '--directory', type=str, help='output directory',
                        default='.')
    # this argument is required, one input file ending with yaml extension
    parser.add_argument('input_file', metavar='file', type=utils.yaml_file,
                        help='input yaml file name')

    args = parser.parse_args()

    if args.verbose:
        print('Verbose mode on')
        print('Input file names:', args.input_file)
        if args.directory:
            print('Output directory:', args.directory)


    with open(args.input_file, encoding='ascii') as f:
        y = yaml.load(f, Loader=yaml.FullLoader)

    # This is the parent(root) tag onto which other tags would be
    # created
    cm = ET.Element('node')
    cm.set('id', 'CM')
    cm.set('address', '0x00000000')

    pprinter = pprint.PrettyPrinter(indent=4)

    # start processing the yaml file
    config = y['config']
    sensor_count = 0 # in 16 bit words
    for c in config:  # loop over entries in configuration (sensor category)
        if args.verbose:
            print("category:",)
            pprinter.pprint(c)
        # if there are several devices in the category, handle the case by iterating over them
        devices = c.get('devices', [])
        device_size = max(len(devices), 1)
        category_size = device_size*len(c['sensors'])*sensor_size(c)
        device = devices.pop(0) if devices else ""

        if args.verbose:
            print("category_size:", category_size)
        while True:
            # if there are devices
            if device:
                pp = ET.SubElement(cm, 'node')
                pp.set('id', device)
            else:
                pp = cm
            for sensor in c['sensors']:
                if args.verbose:
                    print(f"sensor: {device}.{sensor}")
                make_node(pp, sensor, c, sensor_count)
                sensor_count += sensor_size(c) // 2
            if devices:
                device = devices.pop(0)
            else:
                break
    tree = ET.ElementTree(cm)
    ET.indent(tree, space='\t')
    # create output file name based on input file, replacing 'yml' with 'xml'
    out_name = os.path.basename(args.input_file)[:-len('.yml')] + '.xml'
    out_name = args.directory + '/' + out_name
    if args.verbose:
        print("writing to file", out_name)
    tree.write(out_name)


if __name__ == "__main__":
    main()
