import flywheel
import logging
#from utils.yaml_decoder_rc2fw import expand_metadata
import sys

log=logging.getLogger(__name__)
log.setLevel("DEBUG")

fw = flywheel.Client()


class RedcapField:
    type_=None
    def __init__(self, meta, record, rc_map):
        self.field_name = meta.get("field_name")
        self.field_label = meta.get("field_label")
        self.field_type = meta.get("field_type")
        self.form_name = meta.get("form_name")
        self.choices = meta.get("select_choices_or_calculations")
        self.meta = meta
        self.record = record
        self.rc_map = rc_map

    def get_fw_object(self):
        fw_dict_out = {self.field_label: {'field_name': self.field_name,
                                          'value': self.value}
                       }
        return (fw_dict_out)

    def get_value(self):
        return (self.value)

    @classmethod
    def factory(cls, type_: str, meta, record, rc_map):
        """Return an instantiated Collector."""
        for sub in cls.__subclasses__():
            if type_.lower() == sub.type_:
                return sub(meta, record, rc_map)
        raise NotImplementedError(f"redcap field type {type_} no supported")




class RCtext(RedcapField):
    type_='text'
    def __init__(self,meta, record, rc_map):
        super().__init__(meta, record, rc_map)
        self.value = self.record.get(self.field_name)

class RCcalc(RedcapField):
    type_='calc'

    def __init__(self,meta, record, rc_map):
        super().__init__(meta, record, rc_map)
        self.value = self.record.get(self.field_name)

class RCyesno(RedcapField):
    type_ = 'yesno'

    def __init__(self,meta, record, rc_map):
        super().__init__(meta, record, rc_map)
        self.value = self.record.get(self.field_name)

        if self.value == '0':
            self.value = 'no'
        elif self.value == '1':
            self.value = 'yes'
        else:
            self.value = ''


class RCcheckbox(RedcapField):
    type_="checkbox"

    def __init__(self, meta, record, rc_map):
        super().__init__(meta, record, rc_map)
        self.value = self.map_field_to_choices()

    def map_field_to_choices(self):
        foi = self.field_name
        record = self.record

        if foi in self.rc_map:
            log.debug(f"found {foi} in self.rc_map")

            working_map = self.rc_map[foi]

            choices = {key: val for key, val in record.items() if key.startswith(foi + "___")}

            value = []
            for key, val in choices.items():
                # As far as i know REDCap separates options with three underscores
                if val != '0':
                    print(val)
                    f, mc = key.split('___')
                    value.append(working_map[mc])

            if len(value) == 1:
                value = value[0]

        return (value)


class RCslider(RedcapField):
    type_='slider'

    def __init__(self,meta, record, rc_map):
        super().__init__(meta, record, rc_map)
        self.value = self.record.get(self.field_name)


class RCtruefalse(RedcapField):
    type_='truefalse'
    def __init__(self, meta, record, rc_map):
        super().__init__(meta, record, rc_map)
        self.value = self.record.get(self.field_name)

        if self.value == '0':
            self.value = 'false'
        elif self.value == '1':
            self.value = 'true'
        else:
            self.value = ''


class RCnotes(RedcapField):
    type_='notes'

    def __init__(self, meta, record, rc_map):
        super().__init__(meta, record, rc_map)
        self.value = self.record.get(self.field_name)


class RCradio(RedcapField):
    type_='radio'

    def __init__(self, meta, record, rc_map):
        super().__init__(meta, record, rc_map)
        self.value = self.map_field_to_choices()

    def map_field_to_choices(self):
        foi = self.field_name
        record = self.record

        field_map = self.rc_map.get(foi)

        if field_map is None:
            log.error(f"No map for field {foi}")
            sys.exit(1)

        code = record.get(self.field_name)
        value = field_map.get(code)
        if code is None:
            log.warning(f"WARNING no code {code} for field {foi} in {field_map}")

        return (value)


class RCdropdown(RedcapField):
    type_='dropdown'

    def __init__(self, meta, record, rc_map):
        super().__init__(meta, record, rc_map)
        self.value = self.map_field_to_choices()

    def map_field_to_choices(self):
        foi = self.field_name
        record = self.record

        field_map = self.rc_map.get(foi)

        if field_map is None:
            log.error(f"No map for field {foi}")
            sys.exit(1)

        code = record.get(self.field_name)
        value = field_map.get(code)
        if code is None:
            log.warning(f"WARNING no code {code} for field {foi} in {field_map}")

        return (value)




class level_export_template:
    def __init__(self, rc_record_field, fw_record_val, mappings, level):
        self.rc_record_field = rc_record_field
        self.fw_record_val = fw_record_val
        self.mappings = mappings
        self.level = level
        self.mapped_values = {}
        self.all_container_maps = {'maps': {}, 'files': {}}
        
        
    def generate_mappings(self, container):
        for map in self.mappings.maps:
            fw_key = list(map.keys())[0]
            rc_field = list(map.values())[0]
            val = expand_metadata(fw_key, container)
            self.mapped_values[rc_field] = val
    
    
    def create_rc_call(self):
        packet = {self.rc_record_field: self.fw_record_val}
        for rc_field, fw_value in self.mapped_values.items():
            packet[rc_field] = fw_value
        #print('packet')
        #print(packet)
        return(packet)
    
    
class export_map:
    def __init__(self, maps={}, files={}):
        self.maps = maps
        self.files = files


