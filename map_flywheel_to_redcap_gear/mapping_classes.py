import flywheel_helpers as fh
import flywheel
from redcap import Project, RedcapError
#fw = flywheel.Client()




class mapper_object:
    def __init__(self, container_type, rc_key='', container_level='', fw_key=''):
        
        if container_type == container_level:
            container_level = 'self'
            
        self.record = {'rc_key': rc_key, 'container_level': container_level, 'fw_key': fw_key}
        self.ctype = container_type
        self.containers = []
        
    def add_container(self, container):
        
        self.containers.append(container)
        
    def to_dict(self):
        c_dict_list = [c.to_dict() for c in self.containers]
        containers = {}
        [containers.update(c) for c in c_dict_list]
        self_dict = {'record': self.record,
                     'containers': containers}
        
        return(self_dict)

        


class container_object:
    def __init__(self, container_id, container_name):
        self.id = container_id
        self.name = container_name
        self.maps = []
        self.files = []
    
    def to_dict(self):
        
        maps = {}
        [maps.update(co.to_dict()) for co in self.maps]
        
        if self.files:
            files = {}
            [files.update(co.to_dict()) for co in self.files]
            
            self_dict = {self.name: {
                            'ContainerID': self.id,
                            'maps': maps,
                            'files': files
                                    }
                        }
            
            
        else:
            self_dict = {self.name: {
                'ContainerID': self.id,
                'maps': maps
            }
            }
        
        if self.id == 'ALL-CONTAINERS' or self.id is None:
            del self_dict[self.name]['ContainerID']
        
        return(self_dict)
    
    def add_map(self, map):
        for key, value in map.items():
            self.maps.append(object_map(key,value))
            



class object_map:

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
    



# 
# 
# class container_object:
#     def __init__(self, container, name="", ctype=None):
#         self.fwid = container.id
#         self.name = name
#         self.record_id = {'key': '', 'container': 'self', 'rc_key': ''}
#         self.mappings = {}
#         self.container = container
#         self.ctype = self.container.container_type
# 
#         if ctype == "project":
#             self.subject = subcontainer(self.container)
#         else:
#             self.subject = None
# 
#         if ctype == "subject":
#             self.session = subcontainer(self.container)
#         else:
#             self.session = None
# 
#         if ctype == "session":
#             self.acquisition = subcontainer(self.container)
#         else:
#             self.acquisition = None
# 
#         self.file = subcontainer(self.container, files=True)
# 

# project = fw.get('5db0759469d4f3001f16e9c1')
# test=container_object(project,'Bsample','project')
# s1=test.subject['sub-15'].session['ses-']
