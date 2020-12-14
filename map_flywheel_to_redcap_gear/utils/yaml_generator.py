import logging
import yaml
import flywheel
from utils.mapping_classes import container_object, mapper_object
from utils import flywheel_helpers as fh

log=logging.getLogger(__name__)
log.setLevel('DEBUG')
log.info(f'log level {log.level} ')



def generate_map_at_level(fw, container, level, record, populate=False, add_all=False):
    
    level_map = mapper_object(container_type=level, **record)

    if add_all:
        all_object = container_object('ALL-CONTAINERS', 'ALL-CONTAINERS')
        level_map.add_container(all_object)

    if populate:
        children = fh.get_iter_children(fw, container, level)

        for child in children:
            child_object = container_object(child.id, fh.get_name(child))
            level_map.add_container(child_object)

    return (level_map)


def generate_subjects(fw, project, record, populate, add_all):
    
    level = 'subject'
    subject_list = {'ethnicity': 'ethnicity_d1',
                    'label': 'fw_id_d1'}

    level_map = mapper_object(container_type = level, **record)

    if add_all:
        all_object = container_object('ALL-CONTAINERS', 'ALL-CONTAINERS')
        level_map.add_container(all_object)

    if populate:
        children = fh.get_iter_children(fw, project, level)

        for child in children:
            child_object = container_object(child.id, fh.get_name(child))
            #child_object.add_map(subject_list)
            level_map.add_container(child_object)
        
    
    return(level_map)



def unique_container_labels(containers):
    labels = [s.label for s in containers]
    duplicates = [x for x in labels if labels.count(x) > 1]
    if duplicates:
        log.error('containers must have unique labels within subject')
        return(False)
    
    return(True)
    
    
def populate_map_from_labels(labels, level_map):

    for label in labels:
        child_object = container_object('ALL-CONTAINERS', label)
        level_map.add_container(child_object)

    return (level_map)


def add_all_to_mapper(level_map):
    all_object = container_object('ALL-CONTAINERS', 'ALL-CONTAINERS')
    level_map.add_container(all_object)
    return(level_map)


def generate_sessions(fw, project, record, populate=False, add_all=False):
    
    level = 'session'
    level_map = mapper_object(container_type=level, **record)
    #session_list = {'age_in_years': 'age_d1'}
    
    if add_all:
        level_map = add_all_to_mapper(level_map)

    if populate:
        subjects = project.subjects()

        unique_labels = set()
        for sub in subjects:
            sub_sessions = sub.sessions()
            if unique_container_labels(sub_sessions):
                [unique_labels.add(ss.label) for ss in sub_sessions]
            else:
                raise Exception('Session names must be unique within subjects')
        
        level_map = populate_map_from_labels(unique_labels, level_map)
            
    return(level_map)


    level_map = generate_map_at_level(fw, project, ctype, record, populate, add_all)

    return (level_map)
    
    
def generate_acquisitions(fw, project, record, populate, add_all):
    level = 'acquisition'
    level_map = mapper_object(container_type=level, **record)

    if add_all:
        level_map = add_all_to_mapper(level_map)

    if populate:
        subjects = project.subjects()

        unique_labels = set()
        for sub in subjects:
            sub_sessions = sub.sessions()
            for ses in sub_sessions:
                acquisitions = ses.acquisitions()
                if unique_container_labels(acquisitions):
                    [unique_labels.add(ss.label) for ss in acquisitions]
                else:
                    raise Exception('acquisitions names must be unique within sessions')
                

        level_map = populate_map_from_labels(unique_labels, level_map)

    return (level_map)
    
    
def populate_files(fw, project, level, level_map):
    
    containers_at_level = level_map[level].containers
    
    for container in containers_at_level:
        children = fw.acquisitions.find(f'parents.project={project.id},label={container.name}')
        
        unique_labels = set()
        for child in children:
            files = child.files
            [unique_labels.add(ss.name) for ss in files]
        
        for ul in unique_labels:
            container.files.append(container_object('ALL', ul))

    return(level_map)



def generate_yaml(api_key, project_id, run_rules, record):

    fw = flywheel.Client(api_key)
    project = fw.get_project(project_id)
    
    subject_list = {}
    main_map = {}
    
    
    ######### Populate Subjects
    populate = run_rules['each_subject']
    add_all = run_rules['all_subjects']
    add_files = run_rules['subject_files']
    
    subjects = generate_subjects(fw, project, record, populate, add_all)
    main_map['subject'] = subjects
    
    if add_files:
        main_map = populate_files(fw, project, 'subject', main_map)


    ######### Populate sessions
    populate = run_rules['each_session']
    add_all = run_rules['all_sessions']
    add_files = run_rules['session_files']

    sessions = generate_sessions(fw, project, record, populate, add_all)
    main_map['session'] = sessions

    if add_files:
        main_map = populate_files(fw, project, 'session', main_map)


    ######### Populate acquisitions
    populate = run_rules['each_acquisition']
    add_all = run_rules['all_acquisitions']
    add_files = run_rules['acquisition_files']

    acquisitions = generate_acquisitions(fw, project, record, populate, add_all)
    main_map['acquisition'] = acquisitions

    if add_files:
        main_map = populate_files(fw, project, 'acquisition', main_map)

    acquisitions = generate_acquisitions(fw, project, record, populate, add_all)
    main_map['acquisition'] = acquisitions
    
    output = {}
    output['subject'] = main_map['subject'].to_dict()
    output['session'] = main_map['session'].to_dict()
    output['acquisition'] = main_map['acquisition'].to_dict()
    
    
    with open('/flywheel/v0/output/Flywheel2Redcap_template.yaml', 'w') as yaml_out:
        yaml_out.write(yaml.dump(output, sort_keys=False))
