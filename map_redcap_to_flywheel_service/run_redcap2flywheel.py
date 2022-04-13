import flywheel
from utils import yaml_decoder_rc2fw as yd
import os
import getpass
import argparse as ap

parser = ap.ArgumentParser(
    description="Uploads metadata from a redcap instance to a flywheel project")

parser.add_argument('-f', '--fwapi', type=str,
                    help="The API key for the Flywheel instance that you are uploading data to")

parser.add_argument('-p', '--projectID', type=str,
                    help="The ID of the Flywheel project you are uploading data to.")

parser.add_argument('-r', '--rcAPI', type=str,
                    help="The API key for the REDCap instance that you are downloading data from.")

parser.add_argument('-u', '--rcURL', type=str,
                    help="The URL of the REDCap instance that you are downloading data from.")

parser.add_argument('-y', '--yamlFile', type=str,
                    help="The full path to the yaml file that describes what metadata to download")


def get_missing_inputs(args):
    if args['fwapi'] is None:
        args['fwapi'] = getpass.getpass(prompt="Please enter your flylwheel API key")

    if args['projectID'] is None:
        args['projectID'] = getpass.getpass(
            prompt='Please enter the ID of the Project to extract data from')

    if args['rcURL'] is None:
        args['rcURL'] = getpass.getpass(
            prompt='Please enter the URL of the REDCap project to upload data to')

    if args['rcAPI'] is None:
        args['rcAPI'] = getpass.getpass(prompt='Please enter your REDCap API token')

    if args['yamlFile'] is None:
        args['yamlFile'] = input('Please enter the location of the flywheel to redcap yaml file')

    return (args)


###################################


if __name__ == '__main__':
    
    args = parser.parse_args().__dict__
    args = get_missing_inputs(args)
    
    fw = flywheel.Client(args['fwapi'])
    project = fw.get_project(args['projectID'])
    
    rc_dict, fw_key_level, fw_key = yd.rc_2_fw(args['yamlFile'], args['rcAPI'], args['rcURL'])
    
    yd.rc_dict_2_fw(project, rc_dict, fw_key_level, fw_key)

