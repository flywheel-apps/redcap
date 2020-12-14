import flywheel
import flywheel_gear_toolkit
import json
import logging
import os
import sys
from utils import yaml_generator as yg

log = logging.getLogger(__name__)


def get_config(gear_context):
    run_rules = {}
    config = gear_context.config
    run_rules['all_subjects'] = config["1a Add Rules for 'all subjects'"]
    run_rules['each_subject'] = config["1b Populate every subject in project"]
    run_rules['subject_files'] = config["1c Add Rules for subject files"]
        
    run_rules['all_sessions'] = config["2a Add Rules for 'all sessions'"]
    run_rules['each_session'] = config["2b Populate every session in project"]
    run_rules['session_files'] = config["2c Add Rules for session files"]

    run_rules['all_acquisitions'] = config["3a Add Rules for 'all acquisitions'"]
    run_rules['each_acquisition'] = config["3b Populate every acquisition in project"]
    run_rules['acquisition_files'] = config["3c Add Rules for acquisition files"]

    record = {'rc_key':'', 'container_level': '', 'fw_key': ''}

    record['rc_key'] = config["4a Redcap record ID variable name (As stored in redcap)"]
    record['container_level'] = config["4b Container type that has redcap ID in metadata"]
    record['fw_key'] = config["4c Metadata field that contains the redcap ID (As stored in flywheel)"]

    return(run_rules, record)


def main(gear_context):
    
    apikey = gear_context.get_input("api_key")["key"]
    run_rules, record = get_config(gear_context)
    fw = flywheel.Client(apikey)
    
    destination = gear_context.destination["id"]
    analysis = fw.get(destination)
    project_id = analysis.parents.project
    
    yg.generate_yaml(apikey, project_id, run_rules, record)
    
    
    









if __name__ == "__main__":

    with flywheel_gear_toolkit.GearToolkitContext(
            config_path='/flywheel/v0/config.json') as gear_context:
        # gear_context.config['debug_gear'] = True
        gll = gear_context.config['Gear Log Level']
        gear_context.init_logging(gll)
        gear_context.log_config()

        # grab environment for gear
        with open('/tmp/gear_environ.json', 'r') as f:
            environ = json.load(f)
            os.environ.update(environ)
            os.environ

            # Add environment to log if debugging
            kv = ''
            log.debug('Environment:')
            for k, v in environ.items():
                kv = k + '=' + v + ' '
                log.debug(kv)
            # log.debug('Environment: ' + kv)

        exit_status = main(gear_context)

    if exit_status != 0:
        log.error('Failed')
        sys.exit(exit_status)

    log.info(f"Report generated successfully {exit_status}.")
