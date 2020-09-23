import flywheel_helpers as fh
import flywheel

fw = flywheel.Client()





def 







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


# write_instructions = {
#                         'write_rcfield': True,
#                         'write_location': True,
#                         'write_map_objects': True,
#                         'write_sub_map_objects': True,
#                         'write_map_object_fields': True,
#                         'write_migrate': True,
#                         'write_field_objects': True,
#                         'write_meta': True,
#                         'write_custom': True,
#                         'write_files': True
#                     }

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

def set_default_write_instructions():
    write_instructions = {
        'write_rcfield': True,
        'write_location': True,
        'write_map_objects': True,
        'write_sub_map_objects': False,
        'write_map_object_fields': False,
        'write_migrate': True,
        'write_field_objects': False,
        'write_meta': True,
        'write_custom': True,
        'write_files': True
    }
    return(write_instructions)


class mapper_object:
    def __init__(self, container_type, record = None):
        self.mappings = []
        self.record = record
        self.ctype = container_type

    def add_map(self,fw_meta, rc_field):
        self.mappings.append(map(fw_meta, rc_field))
        
    def to_dict(self):
        mapped_dicts = [m.to_dict for m in self.mappings]
        self_dict = {'record': self.record,
                     'map': mapped_dicts}
        
        return(self_dict)
        


class map:

    def __init__(self, fw_meta, rc_field):
        self.fw_meta = fw_meta
        self.rc_field = rc_field

    def to_dict(self):
        return ({self.fw_meta: self.rc_field})



class subcontainer:
    def __init__(self, parent, files=False):
        self.parent = parent
        self.files = files
    
    def __getitem__(self, item):
        
        if self.files:
            children = self.parent.files
            child = [chld for chld in children if chld.name == item][0]
            name = child.name
        else:
            children = fh.get_children(self.parent)
            child = [chld for chld in children if chld.label == item][0]
            name = child.label
            
        fwid = child.id
        ctype = child.container_type
        
        return(container_object(child, name, ctype))
    





class container_object:
    def __init__(self, container, name="", ctype=None):
        self.fwid = container.id
        self.name = name
        self.record_id = None
        self.mappings = {}
        self.container = container
        self.ctype = self.container.container_type

        if ctype == "project":
            self.subject = subcontainer(self.container)
        else:
            self.subject = None

        if ctype == "subject":
            self.session = subcontainer(self.container)
        else:
            self.session = None

        if ctype == "session":
            self.acquisition = subcontainer(self.container)
        else:
            self.acquisition = None

        self.file = subcontainer(self.container, files=True)


project = fw.get('5db0759469d4f3001f16e9c1')
test=container_object(project,'Bsample','project')
s1=test.subject['sub-15'].session['ses-']
