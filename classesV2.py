import flywheel_helpers as fh
import flywheel

fw = flywheel.Client()








class mapper_object:
    def __init__(self, container_type, record='', record_container='self'):
        self.mappings = {}
        self.record = {'rc_key': record, 'container': record_container, 'fw_key':''}
        self.ctype = container_type

    def add_map(self, fw_meta, rc_field):
        self.mappings[fw_meta] = rc_field
        
    def to_dict(self):
        self_dict = {'record': self.record,
                     'map': self.mappings}
        
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
        self.record_id = {'key': '', 'container': 'self', 'rc_key': ''}
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
