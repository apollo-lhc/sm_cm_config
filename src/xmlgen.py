#! /usr/bin/env python
# generate the XML file from the YAML file

import xml.etree.ElementTree as ET
import argparse
import os
from pprint import pprint
import yaml

import utils # local import

def type_to_size(thedict: dict) -> int:
    """calculate the size of the sensor in bytes"""
    sz = 2 # default size
    if '32' in thedict['type']:
        sz = 4
    elif 'char' in thedict['type']:
        sz = 1
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
    theaddr = int(address/2)
    thenode.set('address', str(hex(theaddr)))
    thenode.set("permission", "r")
    width = type_to_size(thedict) # size in bytes
    theformat = type_to_format(thedict) # format of the sensor
    thenode.set('format', theformat)

    # char type sensors are handled differently
    if thedict['type'] == 'char':
        thenode.set('mode', "incremental")
        thenode.set('size', str(hex(thedict['size'])))
    else: # all other types have masks
        mask = (1 << width) - 1
        is_odd = address % 2
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
    parser.add_argument('-d', '--directory', type=str, help='output directory')
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
        if args.verbose:
            pprint(y)

    #This is the parent(root) tag
    #onto which other tags would be
    #created
    cm = ET.Element('node')
    cm.set('id', 'CM')
    cm.set('address', '0x00000000')

    # start processing the yaml file
    config = y['config']

    for c in config:  # loop over entries in configuration (sensor category)
        # if there are several devices in the category, handle the case by iterating over them
        if "devices" in c:
            devices = c['devices']
            device = devices.pop(0)
        else: # if there are no devies, create a list with one empty string
            devices = []
            device = ""
        while True:
            # if there are devices
            if device:
                pp = ET.SubElement(cm, 'node')
                pp.set('id', device)
            else:
                pp = cm
            for sensor in c['sensors']:
                if args.verbose:
                    print("sensor:", sensor)
                node = make_node(pp, sensor, c, device)
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
