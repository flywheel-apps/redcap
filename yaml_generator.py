from classes import container_object, mapping_object, field_object, location_object
import logging
import os
import yaml
import flywheel


log=logging.getLogger(__name__)
log.setLevel('DEBUG')
log.info(f'log level {log.level} ')

container_meta_dict = {'project': ['label',
                                   'description'],
                       'subject': ['label',
                                   'type',
                                   'firstname',
                                   'lastname',
                                   'sex',
                                   'age',
                                   'cohort',
                                   'race',
                                   'ethnicity',
                                   'species',
                                   'strain'],   
                       'session': ['label',
                                   'timestamp',
                                   'age',
                                   'weight',
                                   'operator',
                                   'uid',
                                   'timezone'],
                       'acquisition': ['label',
                                       'uid',
                                       'timestamp'],
                       'file': ['classification','name','modality','type']}

write_instructions = {
    'write_rcfield': True,
    'write_location': True,
    'write_map_objects': True,
    'write_sub_map_objects': True,
    'write_map_object_fields': True,
    'write_migrate': True,
    'write_field_objects': True,
    'write_meta': True,
    'write_custom': False,
    'write_files': False
}


fo_key = 'write_field_objects'
loc_key = 'write_location'
rcf_key = 'write_rcfield'
wm_key = 'write_migrate'
wmo_key = 'write_map_objects'
wsmo_key = 'write_sub_map_objects'
wmof_key = 'write_map_object_fields'
wmeta_key = 'write_meta'
wc_key = 'write_custom'
wf_key = 'write_files'





def populate_container(container, object=None, migrate=True, default='Flywheel'):
    
    if container.container_type not in container_meta_dict:
        log.warning(f"container type {container.container_type} not recognised. "
                    f"Valid types are {container_meta_dict.keys()}")

        return ({})
    
    if object is None:
        mainlabel = container.label
        new_object = container_object(mainlabel, write_instructions)
    else:
        new_object = object
        
    meta_keys = container_meta_dict[container.container_type]
    meta_dict = dict.fromkeys(meta_keys)
    
    for key in meta_keys:
        meta_dict[key] = container.get(key, None)
    new_object.add_metadata(meta_dict)
    
    if container.info != {}:
        info_dict = container.info
        new_object.add_custominfo(info_dict)
    
    if container.files != []:
        new_object.add_files(container.files)
        

    return(new_object)


def make_project_yaml(project_ID):
    
    
    l1 = location_object('default')
    l1.event = 'event1'
    l1.arm = None
    l1.form = 'FlywheelMetadata'
    
    l2 = location_object('Demographics')
    l2.event = 'event1'
    l2.arm = None
    l2.form = 'SubjectDemographics'
    
    main_dict = {'Locations':[l1.export(),l2.export()],
                 'Project': {},
                 'Subjects': {},
                 'Sessions': {},
                 'Acquisitions': {}}
    
    project = fw.get(project_ID)
    
    project_container = container_object('Project', write_instructions)
    project_container = populate_container(project, project_container)
    main_dict['Project'].update(project_container.export())
    
    subject_object = container_object('Subjects',write_instructions)
    
    for subject in project.subjects():
        subject = subject.reload()
        subject_object = populate_container(subject, subject_object)
    
    session_object = container_object('Sessions',write_instructions)
    acquisition_object = container_object('Acquisitions', write_instructions)
    
    
    for session in project.sessions():
        session = session.reload()
        session_object = populate_container(session,session_object)
        
        for acquisition in session.acquisitions():
            acquisition = acquisition.reload()
            acquisition_object = populate_container(acquisition, acquisition_object)
    
    main_dict['Subjects'].update(subject_object.export())
    main_dict['Sessions'].update(session_object.export())
    main_dict['Acquisitions'].update(acquisition_object.export())
    
    return(main_dict)
        
        



fw=flywheel.Client()

# ses_container = fw.get('5ebda220bfda5102856aa0cd')
# ses_object = populate_container(ses_container)
# e=ses_object.export()
# print(yaml.dump(e, sort_keys=False))

test_dict = make_project_yaml('5daa044a69d4f3002a16ea93')
with open('/Users/davidparker/Desktop/TestYaml.yaml', 'w') as yaml_out:
    yaml_out.write(yaml.dump(test_dict, sort_keys=False))

