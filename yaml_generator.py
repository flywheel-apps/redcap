from classes import container_object, mapping_object, field_object, location_object
import logging
import os
import yaml
import flywheel
from classesV2 import mapper_object

log=logging.getLogger(__name__)
log.setLevel('DEBUG')
log.info(f'log level {log.level} ')





def make_project_yaml(dict, container_type):
    
    mapper = mapper_object(container_type)
    for key, value in dict.items():
        mapper.add_map(key,value)
        
    return(mapper)


subject_list = {'ethnicity': 'ethnicity_d1',
                'label': 'fw_id_d1'}

session_list = {'age_years': 'age_d1',
                "info.BIDS.Subject": 'bids_sub_d1'}

file_list = {"classification.Intent": 'scan_intent_s1',
             "info.BIDS.Folder]": 'scan_bids_folder_s1'}

acquisition_list = {'label': 'acq_label_d1'}

subjects = make_project_yaml(subject_list, 'subject')
subjects.record = {'rc_key': 'subject_id', 'container': 'self', 'fw_key': 'label'}
sessions = make_project_yaml(session_list, 'session')
sessions.record = {'rc_key': 'subject_id', 'container': 'subject', 'fw_key': 'label'}
acquisitions = make_project_yaml(acquisition_list,'acquisition')
acquisitions.record = {'rc_key': 'subject_id', 'container': 'subject', 'fw_key': 'label'}
files = make_project_yaml(file_list, 'file')
files.record = {'rc_key': 'subject_id', 'container': 'subject', 'fw_key': 'label'}


master_dict = {}

l = [subjects, sessions,acquisitions, files]

for ll in l:
    master_dict[ll.ctype]=ll.to_dict()


with open('/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Redcap/map_flywheel_to_redcap/TestYaml.yaml', 'w') as yaml_out:
    yaml_out.write(yaml.dump(master_dict, sort_keys=False))
    







# ses_container = fw.get('5ebda220bfda5102856aa0cd')
# ses_object = populate_container(ses_container)
# e=ses_object.export()
# print(yaml.dump(e, sort_keys=False))

# test_dict = make_project_yaml('5daa044a69d4f3002a16ea93')
# with open('/Users/davidparker/Desktop/TestYaml.yaml', 'w') as yaml_out:
#     yaml_out.write(yaml.dump(test_dict, sort_keys=False))

