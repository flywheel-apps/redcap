

def get_children(container):

    ct = container.container_type
    if ct == "project":
        children = container.subjects()
    elif ct == "subject":
        children = container.sessions()
    elif ct == "session":
        children = container.acquisitions()
    elif ct == "acquisition" or ct == "analysis":
        children = container.files
    else:
        children = []

    return children


def get_parent(fw, container):

    ct = container.container_type

    if ct == "project":
        parent = fw.get_group(container.group)
    elif ct == "subject":
        parent = fw.get_project(container.project)
    elif ct == "session":
        parent = container.subject
    elif ct == "acquisition":
        parent = container.get_session(container.session)
    elif ct == "analysis":
        parent = fw.get(container.parent["id"])
    else:
        parent = None

    return parent


def get_subject(fw, container):

    ct = container.container_type

    if ct == "project":
        subject = None
    elif ct == "subject":
        subject = container
    elif ct == "session":
        subject = container.subject
    elif ct == "acquisition":
        subject = fw.get_subject(container.parents.subject)
    elif ct == "file":
        subject = get_subject(container.parent.reload())
    elif ct == "analysis":
        sub_id = container.parents.subject
        if sub_id is not None:
            subject = fw.get_subject(sub_id)
        else:
            subject = None

    return subject


def get_session(fw, container):

    ct = container.container_type

    if ct == "project":
        session = None
    elif ct == "subject":
        session = None
    elif ct == "session":
        session = container
    elif ct == "acquisition":
        session = fw.get_session(container.parents.session)
    elif ct == "file":
        session = get_session(container.parent.reload())
    elif ct == "analysis":
        ses_id = container.parents.session
        if ses_id is not None:
            session = fw.get_session(ses_id)
        else:
            session = None

    return session


def get_acquisition(fw, container):
    ct = container.container_type

    if ct == "project":
        acquisition = None
    elif ct == "subject":
        acquisition = None
    elif ct == "session":
        acquisition = None
    elif ct == "acquisition":
        acquisition = container
    elif ct == "file":
        acquisition = get_acquisition(container.parent.reload())
    elif ct == "analysis":
        ses_id = container.parents.acquisition
        if ses_id is not None:
            acquisition = fw.get_acquisition(ses_id)
        else:
            acquisition = None

    return acquisition


def get_analysis(fw, container):
    ct = container.container_type

    if ct == "project":
        analysis = None
    elif ct == "subject":
        analysis = None
    elif ct == "session":
        analysis = None
    elif ct == "acquisition":
        analysis = None
    elif ct == "file":
        analysis = get_analysis(container.parent.reload())
    elif ct == "analysis":
        analysis = container

    return analysis


def get_project(fw, container):
    ct = container.container_type

    if ct == "project":
        project = container
    elif ct == "subject":
        project = fw.get_project(container.parents.project)
    elif ct == "session":
        project = fw.get_project(container.parents.project)
    elif ct == "acquisition":
        project = fw.get_project(container.parents.project)
    elif ct == "file":
        project = get_project(container.parent.reload())
    elif ct == "analysis":
        project = fw.get_project(container.parents.project)

    return project


def get_parent_at_level(fw, container, level):

    if level == "project":
        parent = get_project(fw, container)
    elif level == "subject":
        parent = get_subject(fw, container)
    elif level == "session":
        parent = get_session(fw, container)
    elif level == "acquistion":
        parent = get_acquisition(fw, container)
    elif level == "analysis":
        parent = get_analysis(fw, container)

    return parent


def generate_path_to_container(
    fw,
    container,
    group=None,
    project=None,
    subject=None,
    session=None,
    acquisition=None,
    analysis=None,
    file=None,
):
    ct = container.container_type
    if ct == "file":
        path_to_file = generate_path_to_container(
            fw,
            container.parent.reload(),
            group,
            subject,
            session,
            acquisition,
            analysis,
        )
    
        fw_path = f"{path_to_file}/{container.name}"
    
    else:
        
        break_to_analysis = False
        
        if group is None:
            group = container.group
            
        fw_path = group
        
        if project is None and not break_to_analysis:
            last_container = get_project(fw, container)
            
            if last_container is not None:
                project = last_container.label
                fw_path += "/" + project
            else:
                break_to_analysis = True
                
        if subject is None and not break_to_analysis:
            last_container = get_subject(fw, container)

            if last_container is not None:
                subject = last_container.label
                fw_path += "/" + subject
            else:
                break_to_analysis = True

        if session is None and not break_to_analysis:
            last_container = get_session(fw, container)

            if last_container is not None:
                session = last_container.label
                fw_path += "/" + session
            else:
                break_to_analysis = True
       
        if acquisition is None and not break_to_analysis:
            last_container = get_acquisition(fw, container)

            if last_container is not None:
                acquisition = last_container.label
                fw_path += "/" + acquisition
            else:
                break_to_analysis = True
        
        if analysis is None or break_to_analysis:
            last_container = get_analysis(fw, container)

            if last_container is not None:
                session = last_container.label
                fw_path += "/" + session
            else:
                break_to_analysis = True
       
    
    return(fw_path)
    

