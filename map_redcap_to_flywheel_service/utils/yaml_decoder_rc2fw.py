import logging
import os
import yaml
import flywheel
from utils import flywheel_helpers as fh
import json
from redcap import Project
import sys

log=logging.getLogger(__name__)
log.setLevel('DEBUG')
log.info(f'log level {log.level} ')



def get_nested_value(container, keys):
    # log.debug(container)
    if container.container_type != 'file':
        container = container.reload()
        label = container.label
    else:
        label = container.name
        
    log.debug(f'container {label}')
    log.debug(f'type: {container.container_type}')

    try:
        key_tree = keys.split('.')
        sub_level = container
        log.debug(key_tree)
        for key in key_tree:
            sub_level = sub_level.get(key)
            log.debug(sub_level)

        value = sub_level


    except Exception as e:
        log.exception(e)
        log.debug('exception')
        log.warning(f"no object {keys} for {container.id}")
        value = None
    
    if isinstance(value, list):
        value = ','.join(value)
    elif isinstance(value, dict):
        value = json.dumps(value)
    value = str(value)
    
    return(value)


def decode_record(fw, container, record):
    log.debug('GETTING RECORD')
    keys = record['fw_key']
    record_container_level = record['container_level']
    
    if record_container_level == 'self':
        rc_record = get_nested_value(container, keys)
    else:
        record_container = fh.get_parent_at_level(fw, container, record_container_level)
        if record_container is None:
            log.error(f'record location must be in a parent container. '\
                      f'level {record_container_level} is  child of {container.container_type}')
            
            raise Exception('Record level must be child')
        
        rc_record = get_nested_value(record_container, keys)
    
    return(rc_record)



def create_import_object(fw, record, map, container):
    #log.debug(container)
    record_object = {}
    fw_record = decode_record(fw, container, record)
    record_object[record['rc_key']] = fw_record
    
    for fw_key, rc_key in map.items():
        log.debug(f'fw_key: {fw_key}')
        log.debug(f'rc_key: {rc_key}')
        try:
            fw_value = get_nested_value(container, fw_key)
        except Exception as e:
            log.exception(e)
            fw_value = 'NA'
        
        log.debug(f'container: {container.container_type}')
        log.debug(f'key/val: {fw_key}, {fw_value}')
        
        
        record_object[rc_key] = fw_value
    
    return(record_object)


def process_container_level(fw, project, level, container_map):
    
    children = fh.get_iter_children(fw, project, level)
    
    records = []
    
    map = container_map['containers']
    record_info = container_map['record']
    
    log.debug('map:')
    log.debug(map)
    log.debug(f'level: {level}')
    log.debug('children')
    log.debug('record')
    log.debug(record_info)
    
    for child in children:
        if level != 'file':
            log.debug('reloading')
            child = child.reload()
        child_object = create_import_object(fw, record_info, map, child)
        records.append(child_object)
        
    return records


def process_yaml_file(fw, project, yaml_file_path):
    
    with open(yaml_file_path) as file:
        dict_in = yaml.full_load(file)
        file.close()
    
    meta_objects = []
    for level, container_map in dict_in.items():
        
        records = process_container_level(fw, project, level, container_map)
        meta_objects.append(records)
    
    return(meta_objects)


def upload_to_redcap(record_objects, rc_project):
    
    for record_object in record_objects:
        for record in record_object:
            print(record)
            rc_project.import_records([record])


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
    

    
    
def main(fwapi, projectID, yamlFile, rcAPI, rcURL):
    
    fw, fw_project, rc_project = test_inputs(fwapi, projectID, yamlFile, rcAPI, rcURL)
    records = process_yaml_file(fw, fw_project, yamlFile)
    upload_to_redcap(records, rc_project)

