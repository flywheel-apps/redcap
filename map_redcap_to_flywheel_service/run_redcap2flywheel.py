import flywheel
from utils import yaml_decoder_rc2fw as yd
import os
import getpass
import argparse as ap

parser = ap.ArgumentParser(
    description="Uploads metadata from a redcap instance to a flywheel project")

parser.add_argument('-r', '--rcAPI', type=str,
                    help="The API key for the source REDCap instance that you are downloading data from.")

parser.add_argument('-u', '--rcURL', type=str,
                    help="The URL of the source REDCap instance that you are downloading data from.")

parser.add_argument('-f', '--fwapi', type=str,
                    help="The API key for the target Flywheel instance that you are uploading data to")

parser.add_argument('-p', '--projectID', type=str,
                    help="The ID of the target Flywheel project you are uploading data to.")

parser.add_argument('-y', '--yamlFile', type=str,
                    help="The full path to the yaml file that describes what metadata to download")


def get_missing_inputs(args):
    if args['fwapi'] is None:
        args['fwapi'] = getpass.getpass(prompt="Please enter your API key of the target Flywheel instance")

    if args['projectID'] is None:
        args['projectID'] = getpass.getpass(
            prompt='Please enter the ID of the target project in Flywheel')

    if args['rcURL'] is None:
        args['rcURL'] = getpass.getpass(
            prompt='Please enter the URL of the source REDCap instance')

    if args['rcAPI'] is None:
        args['rcAPI'] = getpass.getpass(prompt='Please enter your REDCap API token for the source REDCap instance')

    if args['yamlFile'] is None:
        args['yamlFile'] = input('Please enter the location of the REDCap to Flywheel .yaml file')

    return (args)


###################################


def main(fwapi, fwprojectID, yamlFile, rcAPI, rcURL):

    # Initialize api connection to flywheel instance and redcap project.
    # A flywheel API key allows you to access anything on the flywheel instance (site)
    # that your loging has permissions to access.
    # A redcap API token allows you ONLY access to one specific project, which is a collection
    # of records.

    fw = flywheel.Client(fwapi)
    project = fw.get_project(fwprojectID)

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
# - create sessions based off forms or records or something?
