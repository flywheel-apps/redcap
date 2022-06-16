import flywheel
import logging
import re
from abc import ABC, abstractmethod

# from utils.yaml_decoder_rc2fw import expand_metadata
import sys

log = logging.getLogger(__name__)
log.setLevel("DEBUG")
fw = flywheel.Client()


class Decoder(ABC):
    """ Decode every data type differnetly because every data type is a special snowflake

    Basically redcap export is not great at consistency and so we need
    custom decoders.

    I wanted to avoid just different if statements, I wanted to reuse as much
    code as possible and find a smart, programatic way to decode the data
    from just the metadata we get from redcap, but it's hard and things are
    so inconsistent it's maddening.  This is my best shot.


    """

    @staticmethod
    @abstractmethod
    def decode(field_name, field_value, field_meta=None, field_names_meta=None):
        pass

    @staticmethod
    def get_field_choices(field_meta):
        """ Extract possible field choices. The field value will always
        be numeric if it's multiple choice (1,2,3, etc).  HOWEVER
        in redcap, these numbers correspond to text:

        1 - "Very happy"
        2 - "somewhat happy"
        3 - "not happy", etc

        So you have to go the the metadata to extract these options.

        SOME metadata like yesno and truefalse don't get these
        options spelled out in the metadata so we have to add them

        Args:
            field_meta: the redcap metadata object that exists for this field

        Returns:
            redcap_reassign_map (dict): a dictionary with keys as numbers
                and values as the corresponding rc text, ex:
                {
                    "1":"Very happy",
                    "2": "somethat happy"...etc
                }
        """
        redcap_reassign_map = {}
        # Handle obnoxious special cases
        if field_meta.get("field_type") == "truefalse":
            redcap_reassign_map["0"] = "false"
            redcap_reassign_map["1"] = "true"
            return redcap_reassign_map

        # THESE ARE THE SAME THING REDCAP
        if field_meta.get("field_type") == "yesno":
            redcap_reassign_map["0"] = "no"
            redcap_reassign_map["1"] = "yes"
            return redcap_reassign_map

        # Outside special cases these options will be in this format for checkbox and radio
        choice_key = "select_choices_or_calculations"
        choice_meta = field_meta.get(choice_key)

        pattern = "(?P<num>\d+),\s?(?P<choice>[^\|]+)\s?"
        choice_map = re.findall(pattern, choice_meta)

        if choice_map:
            redcap_reassign_map = {
                str(kv[0]).lower().strip(): kv[1] for kv in choice_map
            }

        return redcap_reassign_map

    @staticmethod
    def get_name_choices(field_names_meta, field_meta):
        """ Special method needed for choose multi.

        when you have a multiple choice (but choose multiple), the field NAME
        itself changes in the record.  For example, in redcap, if you name
        the field "choose_many", and the user selects three options from the
        possible list, the record will show it as:
            "choose_many___1: 0
             choose_many___2: 1
             choose_many___3: 1"

        and in the field_name metadata (DIFFERENT from the regular metadata)
        it has a section that looks like:
         {
            'original_field_name': 'choose_many',
            'choice_value': '2',
            'export_field_name': 'choose_many___2'
        }

        and in the original metadata for "choose_many" you'll have:

         {
            'field_name': 'choose_many',
            ...
            'select_choices_or_calculations': '1, choice 1 text | 2, choice 2 text | ...etc',
            ...
        }

        SO YOU HAVE TO:
            1. see if the field value is 1 or zero
            2. extract the original field name
            3. see what the "choice_value" is in the field_name metadata
            4. see what that choice corresponds to in the orignal metadata

        jfc.

        And yes maybe you could shortcut that The digit at the end of the
        underscores corresponds to the choice value, but I'm not taking
        chances.  fewer assumptions and more direct work from the metadata
        increases the likelihood that this will handle unforseen cases.

        Args:
            field_names_meta:
            field_meta:

        Returns:
            choices (dict): a dict with the field_name and its corresponding choice value:
                {
                    "choose_many___1": "1",
                    "choose_many___2": "2",
                    ...etc
                }


        """
        choices = {f.get('export_field_name'): f.get('choice_value') for f in field_names_meta if f.get('original_field_name') == field_meta.get('field_name')}
        return choices

class DecodeBasic(Decoder):
    """ Basic decoder just returns the value in the record
    """
    @staticmethod
    def decode(field_name, field_value, field_meta=None, field_names_meta=None):
        return field_value

class DecodeChooseOne(Decoder):
    """ Choose 1 decoder must translate between numbers and the corresponding
    text for that number label.

    """
    @staticmethod
    def decode(field_name, field_value, field_meta=None, field_names_meta=None):
        # If there's no value, return nothing
        if not field_value:
            return ''

        # Otherwise try to decode it.  Get the field choices for this
        # object from the field metadata and translate.
        field_choices = Decoder.get_field_choices(field_meta)
        value = field_choices.get(field_value)
        if value is None:
            log.warning(f"WARNING no code {field_value} for field {field_name} in {field_choices}")
        return value

class DecodeChooseMany(Decoder):

    @staticmethod
    def decode(field_name, field_value, field_meta=None, field_names_meta=None):
        """ decodes a field value for a choose-multiple redcap option

        Args:
            field_name (str): the field name we're evaluating
            field_value (list): a list of the chosen values for the field
            rc_map (dict): a dictionary mapping of field names to value/label combos

        Returns:

        """

        # So stupid.  Translate from field name to choice number to choice
        # text label.
        name_choices = Decoder.get_name_choices(field_names_meta, field_meta)
        field_choices = Decoder.get_field_choices(field_meta)

        if field_value == '0':
            return ''

        choice_name = name_choices.get(field_name)
        choice_value = field_choices.get(choice_name)

        return choice_value




FACTORY = {
    "text": DecodeBasic,
    "calc": DecodeBasic,
    "yesno": DecodeChooseOne,
    "checkbox": DecodeChooseMany,
    "slider": DecodeBasic,
    "truefalse": DecodeChooseOne,
    "notes": DecodeBasic,
    "radio": DecodeChooseOne,
    "dropdown": DecodeChooseOne
}


class RedcapField:
    """
    This is an object in python that represents a redcap field, filled with metadata

    There are a number of strange things that redcap does that I try to account for.

    I will talk about the field specific ones here:

    - when you have a multiple choice (but choose 1), the field value will
        always be number (0,1,2,3, etc).  You then need to go to the "metadata"
        section that has metadata on all the fields, and see what each number
        represents (the label given to that choice on the form).
    - when you have a multiple choice (but choose multiple), the field NAME
        itself changes in the record.  For example, in redcap, if you name
        the field "choose_many", and the user selects three options from the
        possible list, the record will show it as:
            "choose_many___1: 0
             choose_many___2: 1
             choose_many___3: 1"
        So, you can't even just search for "choose_many" in the record, you first
        need to see if "choose_many" exists,
    - yesno and truefalse are different, will be represented as "yesno", and "truefalse",
        but will NOT get the metadata key that tells you 0=yes or 0=false.

    """
    type_ = None

    def __init__(self, orig_field_name, full_meta, field_names, record, repeating=False):
        # Seems annoying but I think I need all this
        # Is this field part of a repeating form?
        self.repeating = repeating

        # Is this field a multiple choice field?  If so we may need to get more than
        # one value from the record.
        self.rfields = self.get_related_fields(orig_field_name, field_names, record)

        # Get the metadata for this particular field
        self.meta = self.get_meta_object(orig_field_name, full_meta, field_names)

        # For convenience extract the field type and form name
        self.field_type = self.meta.get('field_type')
        self.form_name = self.meta.get('form_name')

        # Determine if we should even export or not (redcap is special, some forms
        # have empty values that you're supposed to ignore because a later record
        # has them filled out)
        self.should_export, self.rnum = self.check_repeat_status(record)

        # Get the correct decoder
        self.decoder = self.factory(self.field_type)

        # Extract the value.  Do this here so you fail on initialization, rather
        # Than export.
        self.decoded_value = self.get_decoded_value(field_names)

    @classmethod
    def factory(cls, field_type):
        return FACTORY[field_type]

    @staticmethod
    def get_related_fields(orig_field_name, field_names, record):
        """ get all fields that are related to this field.

        For example, a field "multi_choice" with three options
        will spawn three fields in the records:
        "multi_choice___1,
         multi_choice___2,
         multi_choice___3"

        You have to find and evaluate those as the true value of
        "multi_choice"

        Args:
            orig_field_name (str): the original (base) field name.  would be "multi_choice"
                in the example above
            field_names (list): would be a list of field name metadata to identify parents
            record (dict): the current record we're working on.

        Returns:
            related_fields (dict): the relevant fields from the record.
            If it's a multi choice field, dict can have multiple items.

            if it's a regular field like "age", dict is length 1:
            {"multi_choice___1": "0",
            "multi_choice___2": 1}
            vs
            {"age": "34"}


        """
        export_field_names = [fn.get('export_field_name') for fn in field_names if fn.get('original_field_name') == orig_field_name]
        related_fields = {fn:record.get(fn) for fn in export_field_names}
        return related_fields

    def get_decoded_value(self, field_names):
        """ uses the decoder to return field values

        """
        values = []
        for fn, fv in self.rfields.items():
            val = self.decoder.decode(fn, fv, field_meta=self.meta, field_names_meta=field_names)
            if val != '':
                values.append(val)

        # If related_fields is length 1, return as a single item. otherwise, return as a list
        # or nothing.
        if len(self.rfields) == 1:
            values = values[0]
        elif len(values) == 0:
            values = ''

        return values


    def get_fw_object(self):
        """ Takes the values in the object and formats into a dict
         them for flywheel

        Returns:
            fw_dict_out (dict): dict formatted for flywheel metadata.

        """
        # May eventually need a way to handle a different field_name vs export_name
        # found in the "export_field_names()" command
        fw_dict_out = {
            self.meta.get('field_label'): {
                "field_name": self.meta.get('field_name'),
                "field_type": self.meta.get('field_type'),
                "value": self.decoded_value
            }
        }

        # Check to see if we should export or not
        if self.should_export:
            if self.repeating:
                fw_dict_out = {self.rnum: fw_dict_out}
            fw_dict_out = {self.form_name: fw_dict_out}
            return fw_dict_out

        else:
            return {}

    def check_repeat_status(self, record):
        """ Check to see if this particular field should be exported or not.

        One example of why you wouldn't bother with an export
        would be if the RECORD I'm looking at is for a repeated form measurement.

        It will still have fields from all the NON repeated forms, but they'll
        just be blank.  Obviously we don't want to overwrite anything with blank
        data, so just don't export.

        It's complicated, trust me.

        """

        repeat_form_key = "redcap_repeat_instrument"
        repeat_num_key = "redcap_repeat_instance"
        should_include = False
        rnum = ''

        # Case one, the record doesn't even have the repeat key in it, so there are not repeating forms.
        # Include all fields in this case
        if repeat_form_key not in record:
            should_include = True
            return should_include, rnum

        # Case two, the record has the form, but it is blank...
        if record.get(repeat_form_key) == '':
            # 2a AND this is not a repeating field, include it because this means it's the record
            # containing all NON repeating forms
            if not self.repeating:
                # No need to consider rnum since it's a non repeating field.
                should_include = True
                return should_include, rnum

            # 2b otherwise if it IS a repeating field, then don't include it because it will be blank here
            return should_include, rnum

        # Case 3, the field IS from the repeating form that this record is showing
        if self.form_name == record.get(repeat_form_key):
            # Get the record number and include it
            rnum = record.get(repeat_num_key)
            should_include = True
            return should_include, rnum

        # Case 4, this record IS for a repeating form, but not THIS fields repeating form
        # ALso catch all for all other cases.
        return should_include, rnum


    @staticmethod
    def get_meta_object(foi, metadata, field_names):
        meta = [m for m in metadata if m.get("field_name") == foi]

        if not meta:
            field = [f for f in field_names if f.get("original_field_name") == foi]
            if not field:
                log.error(f"no redcap field match for {foi}")
                sys.exit(1)

            field = field[0]

            # If we're here it's some weird field that just indicates if the form is completed
            form_name = foi
            if foi.endswith("_complete"):
                form_name = foi[: -len("_complete")]

            meta = [
                {
                    "field_type": "dropdown",
                    "field_name": field["original_field_name"],
                    "field_label": field["export_field_name"],
                    "form_name": form_name,
                    "select_choices_or_calculations": "0, Incomplete | 1, unverified | 2, complete",
                }
            ]

        return meta[0]



