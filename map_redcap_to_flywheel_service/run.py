import flywheel
from utils import yaml_decoder_rc2fw as yd
import os

fw =flywheel.Client()

rc_api = os.environ['RCAPI_FW']
rc_url = os.environ['RCURL_FW']

project = fw.get('5db0759469d4f3001f16e9c1')
yamlFile = '/Users/davidparker/Documents/Flywheel/SSE/MyWork/Gears/Redcap/redcap/map_redcap_to_flywheel_service/example_template.yaml'

rc_dict, fw_key_level, fw_key = yd.rc_2_fw(yamlFile, rc_api, rc_url)
yd.rc_dict_2_fw(project, rc_dict, fw_key_level, fw_key)

# Add forms
