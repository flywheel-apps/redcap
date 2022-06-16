import flywheel
import logging
import utils.RCfield_classes as rfc
import collections
import numpy as np

log = logging.getLogger(__name__)
log.setLevel("DEBUG")

fw = flywheel.Client()


class RedcapRecord:
    """ class to represent a redcap record, or a group of records for a given recordID

        This class handles grouping raw records, and also handles generating the
        dictionary representation for upload to flywheel by interacting with the
        RedcapField class.

    """
    def __init__(self, full_meta, field_names, records):
        self.full_meta = full_meta
        self.field_names = field_names
        self.records = records
        self.repeat_fields = self.identify_repeat_fields()

    def identify_repeat_fields(self):
        """ Redcap handles repeating forms strangely.  Let's say you have two forms,
        one is only filled out once, the other is filled out multiple times. If the
        multi-form is filled out twice, for example, Redcap will generate THREE
        json objects for this subject, EACH object will have a key for every field
        from all the forms.  The first json object will only have values for the
        non-repeating fields, the second object will only have values for the
        first fillout of the repeating form, the third object will only have values
        for the second fillout of the repeating form.

        This checks through the records and looks for form names that are repeating.
        Having these values makes it easier to handle repeating fields later.

        For the example above it could return the 3 jsons:
        {
            'record_id': 'ID',
            'redcap_repeat_instrument': '',
            'redcap_repeat_instance': '',
            'single_form_field': 'value'
            'repeating_form_field': ''
        },
        {
            'record_id': 'ID',
            'redcap_repeat_instrument': 'repeating_form',
            'redcap_repeat_instance': '1',
            'single_form_field': ''
            'repeating_form_field': 'first value'
        },
        {
            'record_id': 'ID',
            'redcap_repeat_instrument': 'repeating_form',
            'redcap_repeat_instance': '2',
            'single_form_field': ''
            'repeating_form_field': 'second value'
        }


        """
        repeating_forms = []
        if len(self.records) == 1:
            return repeating_forms

        repeating_forms = set([r.get("redcap_repeat_instrument") for r in self.records if r .get("redcap_repeat_instrument")])

        repeating_fields = set([field.get('field_name') for field in self.full_meta if field.get('form_name') in repeating_forms])
        [repeating_fields.add(f"{form}_complete") for form in repeating_forms]

        return repeating_fields


    @classmethod
    def GetRecordGroups(cls, full_meta, field_names, records, id_key):
        """ Group records by identifying record ID.

        Args:
            full_meta (dict): the full field metadata from Project.metadata
            field_names (list): extra metadata information on field names and field types
            records (list): a list of redcap records, which are dicts
            id_key (str): the field name in redcap that identifies the record "id".

        Returns:
            record_groups (dict): a dictionary in the format {redcap ID: record object for that ID}

        """

        # Get all the unique record IDs
        uids = set([r.get(id_key) for r in records])
        log.info(f"found {len(records)} records")
        log.info(f"found {len(uids)} unique IDs")

        record_groups = {}

        # Loop through and extract matching records
        for id in uids:
            user_records = [r for r in records if r.get(id_key) == id]
            # Create the record object for this group of records.
            record_groups[id] = RedcapRecord(full_meta, field_names, user_records)

        return record_groups


    def get_record_dicts(self, fields_of_interest):
        """ generate the fw-compatible dictionary of redcap field values.

        loops through all records stored in this object and compiles them into a single
        dict, implementing logic to determine the structure/values

        Args:
            fields_of_interest (list): a list of fields we want to export.

        Returns:
            record_dict (dict): the fw-compatible dictionary representing all the redcap
                fields specified in fields_of_interest

        """
        record_dict = {}
        # Loop through all the records in this object (for this ID)
        for record in self.records:
            record_objects = []
            # Loop through fields of interest to extract them
            for foi in fields_of_interest:
                # Create RedcapField objects for each field
                repeating = foi in self.repeat_fields
                field_object = rfc.RedcapField(foi, self.full_meta, self.field_names, record, repeating)

                # Check if this field should be appended or not (ex, ignore if blank because of repeating measures)
                if field_object:
                    record_objects.append(field_object)

            for obj in record_objects:
                record_dict = merge_dicts(record_dict, obj.get_fw_object(), False)

        return record_dict



def merge_dicts(dest, update, overwrite):

    for k, v in update.items():
        if isinstance(v, collections.abc.Mapping):
            dest[k] = merge_dicts(dest.get(k, {}), v, overwrite)
        else:
            # Flywheel doesn't like numpy data types:
            if type(v).__module__ == np.__name__:
                v = v.item()

            if k in dest:
                if overwrite:
                    dest[k] = v
                else:
                    pass
            else:
                dest[k] = v

    return dest
