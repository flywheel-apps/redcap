import logging
import os
import yaml
import flywheel
from utils import flywheel_helpers as fh
import utils.RCrecords_classes as rrc
import json
from redcap import Project
import sys


log=logging.getLogger(__name__)
log.setLevel('DEBUG')
log.info(f'log level {log.level} ')


def test_inputs(fw_api, fw_project_id, yaml_file, rc_api, rc_url):

    # Fail early, fail often
    try:
        fw = flywheel.Client(fw_api)
    except Exception as e:
        print('ERROR - invalid flywheel API, or site is unreachable')
        print('Try copy/pasting these values to ensure accuracy')
        print(e)
        sys.exit(1)

    try:
        fw_project = fw.get(fw_project_id)
    except Exception as e:
        print(f'ERROR - invalid flywheel project ID {fw_project_id}, or site is unreachable')
        print('Try copy/pasting these values to ensure accuracy')
        print(e)
        sys.exit(1)

    try:
        rc_project = Project(rc_url, rc_api)
    except Exception as e:
        print(f'ERROR - invalid redcap project url {rc_url} or api key, or site is unreachable')
        print('Try copy/pasting these values to ensure accuracy')
        print(e)
        sys.exit(1)

    if not os.path.isfile(yaml_file):
        print(f'ERROR - yaml file {yaml_file} does not exist')
        sys.exit(1)

    return(fw, fw_project, rc_project)


def build_redcap_dict(fields_of_interest, project, recordid):
    """ perform some logic to intelligently create a metadata dictionary of redcap data for upload to flywheel

    Special cases are:
     - repeated instances (forms that a subject fills out multiple times)
     - choose multiple checkboxes
     - form "complete" indicators
     - yesno vs truefalse

    Args:
        fields_of_interest: the field names that we will be exporting FROM redcap TO flywheel
        project: the flywheel project that we will be exporting the data TO
        recordid: the redcap field that contains the redcap record ID

    Returns:
        redcap_objects: a dictionary of {redcap ID: {redcap metadata dictionary}}
    """

    try:
        # Ensure the record_id (-> def_field) is one of the fields of interest
        if project.def_field not in fields_of_interest:
            fields_of_interest.append(project.def_field)

        log.info(f"Fields of interest: {fields_of_interest}")

        # Retrieve a list of dictionaries containing records of each field of
        # interest for each entry in the RC database
        records = project.export_records(fields=fields_of_interest)
        full_metadata = project.metadata
        field_names = project.export_field_names()

    except Exception as e:
        log.error(f"Error querrying REDCap for fields {fields_of_interest}")
        log.exception(e)
        sys.exit(1)

    # Use the redcap records class to take the redcap records, and group them based on record ID
    grouped_records = rrc.RedcapRecord.GetRecordGroups(full_metadata, field_names, records, recordid)

    redcap_objects = {}

    # loop through the returned groups, convert them into dictionaries that flywheel can read for upload
    for current_id, record_group in grouped_records.items():

        # Create a dictionary representation of all the records for this ID
        record_dict = record_group.get_record_dicts(fields_of_interest)
        print(f"## Subject ID: {current_id}")
        # Store these for later upload (could be done here I suppose)
        redcap_objects[current_id] = record_dict

    return redcap_objects


def generate_redcap_dict(yamlFile='', rc_api='', rc_url=''):

    # Load the yaml file and decode it
    with open(yamlFile) as file:
        dict_in = yaml.full_load(file)
        file.close()

    # record tells us about the redcap record ID
    # (what field it is in redcap and where it is in flywheel
    record = dict_in["record"]

    # Fields tells us what redcap fields to import.  Deliberately opt-in to prevent
    # accidental PHI ingest.  Meaning, there is no Lazy "Ingest All Fields" option, you have to
    # Review and approve the fields you're bringing into flywheel.
    fields = dict_in["fields"]

    # Explicitly extract relevant info from the record (where it's stored)
    fw_key_level = record['container_level']
    fw_key = record['fw_key']
    rc_key = record['rc_key']

    # Get the redcap project
    project = Project(rc_url, rc_api)

    # Build the redcap dictionary for upload to flywheel
    rc_dict = build_redcap_dict(fields, project, rc_key)
    return(rc_dict, fw_key_level, fw_key)





def expand_metadata(meta_string, container):
    """Access dotty notation metadata.

    Made before I knew about dotty-dict and stuff.

    meta_string can be "label", or "info.test.val1" or whatever
    Args:
        meta_string: a string leading to container metadata
        container: the container to find the metadata on

    Returns: the specified metadata value

    """
    metas = meta_string.split('.')
    ct = container.container_type
    name = fh.get_name(container)

    # First value has to be a getattr, as it could be "label", "id", "age", anything.
    first = metas.pop(0)
    val = getattr(container, first)
    temp_container = val
    for meta in metas:
        # After this, we're assuming they're in the "info" section, which is a dict, and
        # can be accessed using simple .get methods
        val = temp_container.get(meta)
        if val:
            temp_container = val
        else:
            log.warning(f'No metadata value {meta_string} found for {ct} {name}')
            return (None)
    return val



def rc_dict_2_fw(fw_project, rc_dict, fw_key_level, fw_key):
    """ Takes a   ~ p a i n s t a k i n g l y ~   curated dictionary and uploads it to a flywheel container

    The dict has the format {key1: {redcap dict}, ... {keyN: {redcap dict}}
    fw_key_level specifies what container level has the corresponding Key1, KeyN, etc
    and fw_key specifies the exact metadata location of the key.

    """

    if fw_key_level != 'subject':
        log.error('Red cap key must be stored on subject level.  Only subject level is supported at this time')
        # Because I said so, that's why.
        raise Exception('Redcap key must be stored at subject level')

    # The only reason this isn't a finder is because I'm not sure how many nested
    # metadata levels are searchable, for example if the flywheel keys are on:
    # subject.info.external.redcap.id or something
    for sub in fw_project.subjects.iter():
        sub = sub.reload()
        # Get the value at the specified key location
        rc_id = expand_metadata(fw_key, sub)
        if rc_id is None:
            continue

        # Update with the appropriate dictionary
        if rc_id in rc_dict:
            sub.update_info({'REDCAP': rc_dict[rc_id]})


