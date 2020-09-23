
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



class container_object:
    def __init__(self, name="", wi=None):
        self.locations = {}
        self.fw_location = "self"
        self.rc_location = "default"
        self.container_type = ""
        self.name = name
        self.migrate = True
        self.metadata = mapping_object('Meta')
        self.custominfo = mapping_object('Info')
        self.files = []

        if wi is not None:
            self.write_instructions = wi
        else:
            self.write_instructions = set_default_write_instructions()
    
    def add_metadata(self, meta_dict):
        self.metadata.map_dict(meta_dict)


    def add_custominfo(self, info_dict):
        self.custominfo.map_dict(info_dict)

    
    def add_file(self, file, wi=None):
        
        if wi is None:
            wi = self.write_instructions
        
        name = file.name
        fnames = [file_dict.name for file_dict in self.files]
        fnum = 1
        
        while name in fnames:
            name = f"{name}_{fnum}"
            fnum += 1
        
        meta_keys = container_meta_dict['file']
        if file.info is not None and file.info != {}:
            meta_keys.append('info')
        
        file_mapper = mapping_object(name)
        file_mapper.write_instructions = wi
        meta_dict = dict.fromkeys(meta_keys)

        for key in meta_keys:
            meta_dict[key] = file.get(key, None)
            
        file_mapper.map_dict(meta_dict)
        self.files.append(file_mapper)
    
    def add_files(self, files):
        for file in files:
            self.add_file(file)
    
    
    def add_export_to_list(self, append_list, map_objects):
        for map_object in map_objects:
            export = map_object.export(self.write_instructions)
            if export is not None and export[map_object.name] != {}:
                append_list.append(export)
        return(append_list)
    

    def export(self):
        export_dict = {"FW_location": self.fw_location,
                       "RC_location": self.rc_location,
                       "migrate": self.migrate,
                       "metadata": [],
                       "custominfo": [],
                       "files": [],
                       "locations": [],
                       "name": self.name,
                       "container_type": self.container_type}

        meta = self.metadata.export()
  
        custom = self.custominfo.export()

        files = []
        files = self.add_export_to_list(files, self.files)
  
        locations = []
        locations = self.add_export_to_list(locations, self.locations)

        export_dict['metadata'] = meta
        export_dict['custominfo'] = custom
        export_dict['files'] = files
        export_dict['locations'] = locations

        if self.write_instructions[wmeta_key] is False:
            export_dict.pop('metadata')
        if self.write_instructions[wc_key] is False:
            export_dict.pop('custominfo')
        if self.write_instructions[wf_key] is False:
            export_dict.pop('files')
        if self.write_instructions[loc_key] is False:
            export_dict.pop('locations')

        return(export_dict)




class mapping_object:
    def __init__(self, name="", level=-1):
        self.rc_location = "default"
        self.migrate = True
        self.redcap_map = []
        self.name = name
        self.level = level + 1
        self.write_instructions = set_default_write_instructions()


    def map_dict(self, pydict, write_instructions=None):
    
        if write_instructions is None:
            write_instructions = self.write_instructions
        for key in pydict.keys():
            if isinstance(pydict[key], dict):
                item = mapping_object(key, self.level)
                item.map_dict(pydict[key], write_instructions)
            else:
                item = field_object(key, key)
            
            item.write_instructions = write_instructions
            if item not in self.redcap_map:
                self.redcap_map.append(item)

    def add_export_to_list(self,append_list,map_objects):
        
        if self.write_instructions[fo_key] is False:
            map_objects = [map for map in map_objects if isinstance(map, mapping_object)]
        if self.write_instructions[wsmo_key] is False:
            map_objects = [map for map in map_objects if isinstance(map, field_object)]
            
        for map_object in map_objects:
            export = map_object.export()
            if export is not None and export[map_object.name] != {}:
                append_list.append(export)
        return(append_list)



    def export(self, write_instructions=None):
        if write_instructions is None:
            write_instructions = self.write_instructions
        export_dict = {"RC_location": self.rc_location,
                       "migrate": self.migrate,
                       "redcap_map": []}

        if write_instructions[wmo_key] is False:
            return(None)
        elif write_instructions[wsmo_key] is False and self.level > 0:
            return(None)
        
        
        rendered_fields = []
        rendered_fields = self.add_export_to_list(rendered_fields, self.redcap_map)
        export_dict['redcap_map'] = rendered_fields

        if write_instructions[loc_key] is False:
            export_dict.pop('RC_location')
        if write_instructions[wm_key] is False:
            export_dict.pop('migrate')
        if write_instructions[wmof_key] is False:
            export_dict.pop('redcap_map')
        
        export_dict = {self.name: export_dict}

        return(export_dict)


class field_object:
    def __init__(self, name, field_name):
        self.rc_location = "default"
        self.field = field_name
        self.migrate = True
        self.name = name
        self.write_instructions = set_default_write_instructions

    def export(self):

        export_dict = {'RC_location': self.rc_location,
                       'field': self.field,
                       'migrate': self.migrate}
        
        
        
        if self.write_instructions[fo_key] is False:
            return(None)
        if self.write_instructions[wm_key] is False:
            export_dict.pop('migrate')
        if self.write_instructions[loc_key] is False:
            export_dict.pop('RC_location')
        if self.write_instructions[rcf_key] is False:
            export_dict.pop('field')
            
        
        export_dict = {self.name: export_dict}

        return(export_dict)



class location_object:
    def __init__(self, name):
        self.event = ''
        self.arm = ''
        self.form = ''
        self.name = name
    
    def export(self):
        export_dict = {'event': self.event,
                       'arm': self.arm,
                       'form': self.form}
        
        export_dict = {self.name: export_dict}
        
        return(export_dict)