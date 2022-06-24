import logging

log = logging.getLogger(__name__)
log.setLevel('DEBUG')


def get_name(container):
    ct = container.container_type
    
    if ct == 'file':
        name = container.name
    else:
        name = container.label
    return(name)

