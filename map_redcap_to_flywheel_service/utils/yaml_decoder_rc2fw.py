import logging
import os
import yaml
import flywheel
from utils import flywheel_helpers as fh
import utils.export_classes as ec
import json
from redcap import Project
import sys

import re

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
    


# def map_fields_to_forms(project):
#     metadata = project.metadata
#     fields2forms = {m['field_name']: m['form_name'] for m in metadata}
#     return(fields2forms)
# 



def get_redcap_mc_map2(project):
    metadata = project.metadata
    choice_key = 'select_choices_or_calculations'
    choice_meta = [m for m in metadata if m.get(choice_key) != '']

    pattern = '(?P<num>\d+),\s?(?P<choice>[^\|]+)\s?'
    redcap_reassign_map = {}

    for cm in choice_meta:
        meta_key = cm['field_name']
        choice_map = re.findall(pattern, cm[choice_key])

        if choice_map:
            cm_map = {str(kv[0]).lower().strip(): kv[1] for kv in choice_map}
            redcap_reassign_map[meta_key] = cm_map

    return(redcap_reassign_map)




def build_redcap_dict(fields_of_interest, project, recordid):
    
    rc_map = get_redcap_mc_map2(project)
    
    pattern = '(?P<num>\d+),\s?(?P<choice>[^\|]+)\s?'
    choice_key = 'select_choices_or_calculations'
    
    
    try:
        if project.def_field not in fields_of_interest:
            fields_of_interest.append(project.def_field)

        rc_records = project.export_records(fields=fields_of_interest)
    except Exception as e:
        log.error(f"Error querrying REDCap for fields {fields_of_interest}")
        log.exception(e)
        sys.exit(1)
    metadata = project.metadata
    field_names = project.export_field_names()
    
    
    redcap_objects = {}
    log.info(f"found {len(rc_records)} records")
    for r in rc_records:
        id = r[recordid]
        #print(r)
        record_object = []
        for foi in fields_of_interest:
            # This must be only one, metadata field_names are enforced unique by redcap

            meta = [m for m in metadata if m.get('field_name') == foi]
            

            if not meta:
                field = [f for f in field_names if f.get('original_field_name')==foi]
                if not field:
                    log.error(f"no redcap field match for {foi}")
                    log.exception(e)
                    sys.exit(1)

                field = field[0]

                # If we're here it's some weird field that just indicates if the form is completed
                form_name = foi
                if foi.endswith('_complete'):
                    form_name = foi[:-len('_complete')]

                meta = [{'field_type': 'truefalse',
                        "field_name": field['original_field_name'],
                        "field_label": field ['export_field_name'],
                        "form_name": form_name,
                        "select_choices_or_calculations":''}]


            meta = meta[0]

            
            
            if meta.get('field_type') == 'slider':
                record_object.append(ec.RCslider(meta, r))
                
            elif meta.get('field_type') == 'truefalse':
                record_object.append(ec.RCtruefalse(meta, r))
                
            elif meta.get('field_type') == 'yesno':
                record_object.append(ec.RCyesno(meta, r))
                
            elif meta.get('field_type') == 'notes':
                record_object.append(ec.RCnotes(meta, r))
                
            elif meta.get('field_type') == 'radio':
                record_object.append(ec.RCradio(meta, r, rc_map))
                
            elif meta.get('field_type') == 'checkbox':
                record_object.append(ec.RCcheckbox(meta, r, rc_map))
                
            elif meta.get('field_type') == 'dropdown':
                record_object.append(ec.RCdropdown(meta, r, rc_map))
                
            elif meta.get('field_type') == 'text':
                record_object.append(ec.RCtext(meta, r))
                
            else:
                log.warning(f"meta field type {meta.get('field_type')} not recognized")
                record_object.append(ec.RCtext(meta, r))
    
        record_dict = {}
        
        for obj in record_object:
                
            form = obj.form_name
            print(form)
            if form not in record_dict:
                record_dict[form] = {}
                
            record_dict[form] |= obj.get_fw_object()
        print(record_dict)
        redcap_objects[id] = record_dict
    
    return(redcap_objects)


def rc_2_fw(yamlFile='',rc_api='', rc_url=''):

    
    if yamlFile=='':
        yamlFile = '/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Redcap/redcap/map_redcap_to_flywheel_service/rc2fw_demo.yaml'
    
    with open(yamlFile) as file:
        dict_in = yaml.full_load(file)
        file.close()

    record = dict_in["record"]
    fields = dict_in["fields"]
    
    fw_key_level = record['container_level']
    fw_key = record['fw_key']
    rc_key = record['rc_key']
    
    if rc_api=='':
        rc_api = os.environ['RCAPI_FW']
        
    if rc_url=='':
        rc_url = os.environ['RCURL_FW']
        
    project = Project(rc_url, rc_api)
    
    rc_dict = build_redcap_dict(fields, project, rc_key)
    return(rc_dict, fw_key_level, fw_key)





def expand_metadata(meta_string, container):
    metas = meta_string.split('.')
    temp_container = container
    ct = container.container_type
    name = fh.get_name(container)

    first = metas.pop(0)
    val = getattr(container, first)
    temp_container = val
    for meta in metas:
        val = temp_container.get(meta)
        if val:
            temp_container = val
        else:
            log.warning(f'No metadata value {meta_string} found for {ct} {name}')
            return (None)
    return (val)



def rc_dict_2_fw(fw_project, rc_dict, fw_key_level, fw_key):
    
    if fw_key_level != 'subject':
        log.error('Red cap key must be stored on subject level.  Only subject level is supported at this time')
        raise Exception('Redcap key must be stored at subject level')
    
    
    for sub in fw_project.subjects.iter():
        sub = sub.reload()
        rc_id = expand_metadata(fw_key, sub)
        
        if rc_id is None:
            continue
        
        if rc_id in rc_dict:
            sub.update_info({'REDCAP': rc_dict[rc_id]})
        
        
        
        
# fw=flywheel.Client()
# project = fw.get('5db0759469d4f3001f16e9c1')
# 
#         
# rc_dict, fw_key_level, fw_key = rc_2_fw()
# rc_dict_2_fw(project, rc_dict, fw_key_level, fw_key)

