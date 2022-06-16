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


def main(fwapi, projectID, yamlFile, rcAPI, rcURL):

    # Initialize the fw client and redcap project
    fw = flywheel.Client(fwapi)
    project = fw.get_project(projectID)

    # Get the dictionary of redcap metadata to upload to flywheel
    rc_dict, fw_key_level, fw_key = yd.generate_redcap_dict(yamlFile, rcAPI, rcURL)
    # Upload
    yd.rc_dict_2_fw(project, rc_dict, fw_key_level, fw_key)


if __name__ == '__main__':
    
    args = parser.parse_args().__dict__
    args = get_missing_inputs(args)
    main(args['fwapi'], args['projectID'],args['yamlFile'], args['rcAPI'], args['rcURL'])
    

# TODO:
# - create subjects if ID doesn't exist
# - create sessions off of