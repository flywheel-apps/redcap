FROM python:3.8-slim-buster

COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt && \
    rm -rf /root/.cache/pip

RUN python3 -c 'import os, json; f = open("/tmp/gear_environ.json", "w"); json.dump(dict(os.environ), f)' 

COPY run.py yaml_generator.py classesV2.py manifest.json flywheel_helpers.py /flywheel/v0/
# Configure entrypoint
ENTRYPOINT ["/bin/bash"]
