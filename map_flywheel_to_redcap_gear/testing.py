from classes_old import container_object, mapping_object, field_object
import logging
import os
import yaml
from redcap import Project
import requests
import json

import flywheel

test_dict = {'class': 3,
             'field2': 'awesome',
             'mother': [1, 2, 3, 4],
             'nested_object': {'na': 1,
                               'nb': 2},
             'double_nested': {'nest1a': {'nest2a': 'front'},
                              'nest1b': {'nest2b': 'back'}}
             }

write_instructions = {
                'write_fields': True,
                'write_location': False,
                'write_objects': True,
                'write_object_fields': True,
                'write_migrate': True,
                'write_nonobjects': True,
                'write_meta': True,
                'write_custom': True,
                'write_files': True
        }

sessions = container_object()
sessions.write_instructions = write_instructions

sessions.name = 'TestSession'
sessions.container_type = 'Session'




meta = mapping_object('Meta')
meta.write_instructions = write_instructions
meta.map_dict(test_dict, write_instructions)
sessions.metadata.append(meta)
e=sessions.export()
print(yaml.dump(e, sort_keys=False))


# RedCap Login (replace this with your RedCap API URL)
URL = 'https://redcapdemo.vanderbilt.edu/api/'

# Enter your REDcap API key
RC_API_KEY = '5D52E9D4C7CBA0EC7A34125733303B17'

# Access the REDCap information we're interested 
# in working with. This command creates a python
# object "rc_project", which allows us to access
# all the REDCap data associated with that project.

# WARNING: For large projects, using this interface
# May be slow, as many of the commands fetch ALL
# The data.  Read more about filtering the results
# to reduce this time
# (https://pycap.readthedocs.io/en/latest/deep.html#exporting-data)

rc_project = Project(URL, RC_API_KEY)
# Successful upload to existing field
test_dict = {'study_id': 'testmanual','creat_1':34}
rc_project.import_records([test_dict])

# 
test_dict = {'study_id': 'testmanual','madeup_1':'test'}
rc_project.import_records([test_dict])




mdata = [{'field_name':'api_uploaded',
         'form_name':'month_1_data',
         'field_type':'text',
         'field_label': 'possibly the only field now'
         }]

print(json.dumps(mdata))

data = {
    'token': '5D52E9D4C7CBA0EC7A34125733303B17',
    'content': 'metadata',
    'format': 'json',
    'data': json.dumps(m),
    'returnFormat': 'json'
}
r = requests.post('https://redcapdemo.vanderbilt.edu/api/', data=data)
print('HTTP Status: ' + str(r.status_code))
print(r.json())




meta = rc_project.metadata
new_meta = {'field_name': 'my_field_2',
 'form_name': 'month_2_data',
 'section_header': '',
 'field_type': 'text',
 'field_label': 'plsWrk2',
 'select_choices_or_calculations': '',
 'field_note': '',
 'text_validation_type_or_show_slider_number': '',
 'text_validation_min': '',
 'text_validation_max': '',
 'identifier': '',
 'branching_logic': '',
 'required_field': '',
 'custom_alignment': '',
 'question_number': '',
 'matrix_group_name': '',
 'matrix_ranking': '',
'field_annotation': ''}

forms = [a['form_name'] for a in meta]
first = forms.index('month_1_data')

meta.insert(first+5, new_meta)


data = {
    'token': '5D52E9D4C7CBA0EC7A34125733303B17',
    'content': 'metadata',
    'format': 'json',
    'data': json.dumps(meta),
    'returnFormat': 'json'
    }

r = requests.post('https://redcapdemo.vanderbilt.edu/api/', data=data)
print('HTTP Status: ' + str(r.status_code))
print(r.json())