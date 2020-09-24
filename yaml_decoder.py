from classes import container_object, mapping_object, field_object, location_object
import logging
import os
import yaml
import flywheel
import flywheel_helpers as fh
import json
from redcap import Project, RedcapError
from classesV2 import mapper_object

log=logging.getLogger(__name__)
log.setLevel('DEBUG')
log.info(f'log level {log.level} ')


rc_url = 'https://redcapdemo.vanderbilt.edu/api/'

with open('/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Redcap/map_flywheel_to_redcap/TestYaml.yaml') as file:
    dict_in = yaml.full_load(file)
    
    file.close()



def get_nested_value(container, keys):
    log.debug(container)
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
    record_container_level = record['container']
    
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
    
    map = container_map['map']
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


def upload_to_redcap(record_objects, api_token):
    
    project = Project(rc_url, api_token)
    
    for record_object in record_objects:
        for record in record_object:
            print(record)
            project.import_records([record])



def test():
    from redcap import Project, RedcapError
    import json
    api_token = '5D52E9D4C7CBA0EC7A34125733303B17'
    url = 'https://redcapdemo.vanderbilt.edu/api/'
    project = Project(url, api_token)
    
    new_record = {'subject_id': 'fwman_sub1',
      'fw_id_d1': 'none',
      'bids_sub_d1': 'NA',
      'age_d1': '1',
      'scan_intent_s1': 'T1',
      'scan_bids_folder_s1': 'trash'}
    
    project.import_records([new_record])


def test2():
    
    fw=flywheel.Client()
    fw_project = fw.get('5db0759469d4f3001f16e9c1')
    api_token = '5D52E9D4C7CBA0EC7A34125733303B17'
    
    yaml_file = '/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Redcap/map_flywheel_to_redcap/TestYaml.yaml'
    records = process_yaml_file(fw, fw_project, yaml_file)
    
    upload_to_redcap(records, api_token)
    
#test2()