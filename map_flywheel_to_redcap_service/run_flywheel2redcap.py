import utils.yaml_decoder as yd
import getpass
import argparse as ap

parser = ap.ArgumentParser(
    description="Uploads metadata from a flywheel project to a redcap instance")

parser.add_argument('-f', '--fwapi', type=str,
                    help="The API key for the Flywheel instance that you are extracting data from.")

parser.add_argument('-p', '--projectID', type=str,
                    help="The ID of the Flywheel project you are extracting data from.")

parser.add_argument('-r', '--rcAPI', type=str,
                    help="The API key for the REDCap instance that you are uploading data to.")

parser.add_argument('-u', '--rcURL', type=str,
                    help="The URL of the REDCap instance that you are uploading data to.")

parser.add_argument('-y', '--yamlFile', type=str,
                    help="The full path to the yaml file that describes what metadata to upload")


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


if __name__=="__main__":
    

    args = parser.parse_args().__dict__
    args = get_missing_inputs(args)
    
    yd.main(**args)
    



