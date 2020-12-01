import flywheel
import utils.flywheel_helpers as fh
import utils.export_classes as ec
import logging
import yaml
from redcap import Project, RedcapError
import re
import os
import sys

log = logging.getLogger(__name__)
log.setLevel('DEBUG')
log.info(f'log level {log.level} ')


def get_rec_val_for_container(container, record):
    rc_rec_level = record['container_level']
    fw_rec_field = record['fw_key']

    if rc_rec_level == 'self':
        fw_rec_val = expand_metadata(fw_rec_field, container)
    else:
        parent = fh.get_parent_at_level(fw, container, rc_rec_level)
        if not parent:
            log.error(f'Error getting parent container {rc_rec_level} from '
                      f'{container.container_type} {fh.get_name(container)}')
            raise Exception('Error getting Parent')
        parent = parent.reload()
        fw_rec_val = expand_metadata(parent, fw_rec_field)

    return (fw_rec_val)

# 
# def process_files(container, files, rc_rec_field, fw_rec_val):
#     file_map = dict()
#     files = {k: v for d in files for k, v in d.items()}
#     print(files)
#     file_map['containers'] = files
#     file_containers = container.files
#     file_calls = get_calls_for_containers(file_containers,
#                                           file_map,
#                                           rc_rec_field,
#                                           fw_rec_val,
#                                           'file')
#     file_map = ec.level_export_template(rc_rec_field, fw_rec_val, file_map, 'file')
#     file_map.generate_mappings(container)
#     return (file_map.create_rc_call())
# 
# 
# def get_calls_for_containers(containers, map, rc_rec_field, fw_rec_val, level):
#     calls = []
#     for container in containers:
#         container_maps = []
#         container = container.reload()
# 
#         if not fw_rec_val:
#             fw_rec_val = get_rec_val_for_container(container, map['record'])
# 
#         container_label = fh.get_name(container)
#         all_container_map = map['containers'].get('ALL-CONTAINERS')
# 
#         print(all_container_map)
#         # Check for all
#         if all_container_map:
#             container_maps.extend(all_container_map.get('maps'))
# 
#             all_container_files = all_container_map.get('files')
#             if all_container_files:
#                 calls.append(
#                     process_files(container, all_container_files, rc_rec_field, fw_rec_val))
# 
#         # Check for specific
#         container_map = map['containers'].get(container_label)
#         if container_map:
#             container_maps.extend(container_map.get('maps'))
#             temp_map = ec.level_export_template(rc_rec_field, fw_rec_val, container_maps, level)
#             temp_map.generate_mappings(container)
#             calls.append(temp_map.create_rc_call())
# 
#             files = container_map.get('files')
#             if files:
#                 calls.append(process_files(container, files, rc_rec_field, fw_rec_val))
# 
#         fw_rec_val = None
# 
#     return (calls)


# def level_map(project, subject_map, session_map, acquisition_map, rc_rec_field=None,
#               fw_rec_val=None):
#     subjects = project.subjects()
#     parent = 'project'
#     child = 'session'
#     level = 'subject'
#     if not rc_rec_field:
#         rc_rec_field = subject_map['record']['rc_key']
# 
#     calls = []
#     sub_calls = get_calls_for_containers(subjects, subject_map, rc_rec_field, fw_rec_val, level)
# 
#     calls.extend(sub_calls)
#     return (calls)
# 

def add_fields_for_container(container, map_labels, search_term):
    sub_container = map_labels.get(search_term)
    new_call = {}
    print(f'----------------- looking for maps in {search_term}')
    if sub_container:
        sub_maps = sub_container.get('maps')
        if sub_maps:
            print(f'Found Maps for {search_term}: {sub_maps}')
            for fw_meta, rc_var in sub_maps.items():
                fw_val = expand_metadata(fw_meta, container)
                new_call.update({rc_var: fw_val})

        sub_files = sub_container.get('files')
        if sub_files:
            child_files = container.files

            for file in sub_files.keys():
                file_match = [cf for cf in child_files if re.match(str(file), cf.name)]

                if file_match:
                    print('Found File')
                    file_match = file_match[0]
                    file_map = sub_files[file]['maps']

                    for fw_meta, rc_var in file_map.items():
                        fw_val = expand_metadata(fw_meta, file_match)
                        new_call.update({rc_var: fw_val})

    return (new_call)


def map_container_and_subcontainers(fw, dict_in, level, parent_container, prev_rc_id, prev_id_level,
                                    prev_fw_key, prev_fw_id):
    level_dict = dict_in.get(level)
    print(level)
    print(dict_in.keys())

    while not level_dict:
        level = fh.child_of_type(level)
        if level is None:
            log.warning('reached end of hierarchy')
            return None
        level_dict = dict_in.get(level)

    children = fh.get_iter_children(fw, parent_container, level)

    map_labels = level_dict['containers']

    rc_id = level_dict['record']['rc_key']
    id_level = level_dict['record']['container_level']
    if id_level == 'self':
        id_level = level
    fw_key = level_dict['record']['fw_key']

    fw_id = None
    print(level)
    call_list = []
    for child in children:

        if id_level == prev_id_level:
            if fw_key == prev_fw_key:
                fw_id = prev_fw_id
        else:
            rec_parent = fh.get_parent_at_level(fw, child, id_level)
            rec_parent = rec_parent.reload()
            fw_id = expand_metadata(fw_key, rec_parent)

        child_call = {rc_id: fw_id}

        child = child.reload()
        child_label = fh.get_name(child)

        # First check for all:

        search_term = 'ALL-CONTAINERS'
        new_call = add_fields_for_container(child, map_labels, search_term)
        child_call.update(new_call)

        search_term = child_label
        new_call = add_fields_for_container(child, map_labels, search_term)
        child_call.update(new_call)

        print(child_call)
        call_list.append(child_call)

        next_level = fh.child_of_type(level)
        if next_level is None:
            log.warning('reached end of hierarchy')
        else:
            children_call = map_container_and_subcontainers(fw, dict_in, next_level, child, rc_id,
                                                            id_level,
                                                            fw_key, fw_id)

            # If children_call is none we've reached the end of the hierarchy.
            if children_call is not None:
                call_list.extend(children_call)
    return (call_list)


def level_map(fw, dict_in, project):
    
    # Our top level is subject
    level = 'subject'
    parent_container = project

    prev_rc_id = None
    prev_id_level = None
    prev_fw_key = None
    prev_fw_id = None

    full_call = map_container_and_subcontainers(fw, dict_in, level, parent_container, prev_rc_id,
                                                prev_id_level,
                                                prev_fw_key, prev_fw_id)

    return (full_call)
# 
# 
# class export_object:
#     def __init__(self, maps, container_name, record, parents, level, id=None):
#         self.record = record
#         self.maps = maps
#         self.container_name = container_name
#         self.id = id
#         self.parents = parents
#         self.level = level
#         self.hierarchy_level = ['file', 'analysis', 'acquisition', 'session', 'subject', 'project']
#         # First iteration will not support analysis uploads because reasons
# 
#     def find_matches(self):
# 
#         parent_project = self.parents.get('project')
#         parent_project = fw.get(parent_project)
# 
#         parent_type = [level for level in self.hierarchy_level
#                        if self.parents.get(level) is not None]
# 
#         if parent_type[0] == 'analysis' or parent_type[1] == 'analysis':
#             log.error('NO ANALYSES')
#             raise Exception("NO ANALYSES")
# 
#         parent_type = parent_type[0]
# 
#         matches = self.get_containers_for_match(parent_project, parent_type)
# 
#     def search_files_for_match(self, container):
# 
#         files = container.files
# 
#         matches = [f for f in files
#                    if re.match(self.container_name, f.name)]
# 
#         return (matches)
# 
#     def get_containers_for_match(self, container, parent_type):
# 
#         iter_children = fh.get_iter_children(fw, container, parent_type)
# 
#         matches = []
#         if self.container_name == 'ALL-CONTAINERS':
#             for child in iter_children:
#                 if self.level == 'file':
#                     child = child.reload()
#                     sub_match = child.files
#                 elif self.level == 'acquisition':
#                     sub_match = child.acquisitions()
#                 elif self.level == 'session':
#                     sub_match = child.sessions.find()
#                 elif self.level == 'subject':
#                     sub_match = child.subjects.find()
#                 matches.extend(sub_match)
# 
#         else:
#             for child in iter_children:
#                 if self.level == 'file':
#                     child = child.reload()
#                     sub_match = self.search_files_for_match(child)
#                 elif self.level == 'acquisition':
#                     sub_match = child.acquisitions.find(f'label=~{self.container_name}')
#                 elif self.level == 'session':
#                     sub_match = child.sessions.find(f'label=~{self.container_name}')
#                 elif self.level == 'subject':
#                     sub_match = child.subjects.find(f'label=~{self.container_name}')
#                 matches.extend(sub_match)
# 
#         return (matches)
# 
#     def process_matches(self, matches):
# 
#         ct = matches[0].container_type
#         for match in matches:
# 
#             if ct != 'file':
#                 match = match.reload()
# 
#             for fw_meta, rc_field in self.map.items():
#                 val = expand_metadata(fw_meta, match)
#                 self.generate_rc_call(match, val, rc_field)
# 
#     def generate_rc_call(self, match, val, rc_field):
#         ct = match.container_type
#         # if self.record.container_level
#         pass


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


def collapse_calls_by_record(calls, record_field):
    record_ids = [c.get(record_field) for c in calls]
    unique_records = set(record_ids)

    collapsed_calls = []
    for ur in unique_records:
        calls_for_record = [c for c in calls if c.get(record_field) == ur]
        single_call = calls_for_record.pop(0)
        for call in calls_for_record:
            single_call.update(call)

        collapsed_calls.append(single_call)

    return collapsed_calls

# 
# def test_export():
#     yaml_file_path = '/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Redcap/map_flywheel_to_redcap/TestYaml.yaml'
#     with open(yaml_file_path) as file:
#         dict_in = yaml.full_load(file)
#         file.close()
# 
#     sub_dict = dict_in['subjects']
#     ses_dict = dict_in['sessions']
#     project = '5db0759469d4f3001f16e9c1'
#     project = fw.get(project)
# 
#     calls = level_map(project, sub_dict, None, None, rc_rec_field=None,
#                       fw_rec_val=None)
# 
#     api_token = '008E87772C45E257A487F15AAEDCBCFE'
#     rc_url = 'https://redcapdemo.vanderbilt.edu/api/'
# 
#     yaml_file = '/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Redcap/map_flywheel_to_redcap/TestYaml.yaml'
#     project = Project(rc_url, api_token)
# 
#     for record in calls:
#         print(record)
#         project.import_records([record])


# def test_export2():
#     yaml_file_path = '/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Redcap/map_flywheel_to_redcap/TestYaml.yaml'
#     with open(yaml_file_path) as file:
#         dict_in = yaml.full_load(file)
#         file.close()
# 
#     sub_dict = dict_in['subjects']
#     ses_dict = dict_in['sessions']
#     project = '5db0759469d4f3001f16e9c1'
#     project = fw.get(project)
# 
#     calls = level_map(project, sub_dict, None, None, rc_rec_field=None,
#                       fw_rec_val=None)
# 
#     api_token = '008E87772C45E257A487F15AAEDCBCFE'
#     rc_url = 'https://redcapdemo.vanderbilt.edu/api/'
# 
#     yaml_file = '/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Redcap/map_flywheel_to_redcap/TestYaml.yaml'
#     project = Project(rc_url, api_token)
# 
#     for record in calls:
#         print(record)
#         project.import_records([record])
# 

# test_export()


def get_redcap_mc_map(project):
    metadata = project.metadata
    choice_key = 'select_choices_or_calculations'
    choice_meta = [m for m in metadata if m.get(choice_key) != '']

    pattern = '(?P<num>\d+),\s?(?P<choice>[^\|]+)\s?'
    redcap_reassign_map = {}

    for cm in choice_meta:
        meta_key = cm['field_name']
        choice_map = re.findall(pattern, cm[choice_key])

        if choice_map:
            cm_map = {str(kv[1]).lower().strip(): kv[0] for kv in choice_map}
            redcap_reassign_map[meta_key] = cm_map

    return (redcap_reassign_map)


def translate_fw_to_rcmc(record, rr_map):
    for r in record.keys():
        if r in rr_map:

            fw_val = record[r]
            fw_val = str(fw_val).lower()

            rr_vals = rr_map[r]

            new_fw_val = rr_vals.get(fw_val)

            if new_fw_val is None:
                log.warning(f'WARNING!\n No match for fw val {record[r]} ' \
                            f'with redcap key {r} and possible matches \n'
                            f'{rr_vals}')
                new_fw_val = '0'

            record[r] = int(new_fw_val)

    return (record)


def get_record_field(main_dict):
    
    record_ids = []
    
    for key, value in main_dict.items():
        rc = value.get('record')
        if rc is not None:
            rc_id = rc.get('rc_key')
            if rc_id is not None:
                record_ids.append(rc_id)
    
    # For now assume that all rc ID's are the same, can be checked later
    return(record_ids[0])


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
        fw_project = fw.get_project(fw_project_id)
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

    return (fw_project, rc_project)


def main(fw, fwapi, projectID, yamlFile, rcAPI, rcURL):

    fw, fw_project, rc_project = test_inputs(fwapi, projectID, yamlFile, rcAPI, rcURL)

    with open(yamlFile) as file:
        dict_in = yaml.full_load(file)
        file.close()
    
    record_field = get_record_field(dict_in)
    
    calls = level_map(fw, dict_in, fw_project)
    calls = collapse_calls_by_record(calls, record_field)

    rr_map = get_redcap_mc_map(rc_project)

    for record in calls:
        print(record)
        record = translate_fw_to_rcmc(record, rr_map)
        rc_project.import_records([record])
    


    
