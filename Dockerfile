FROM ubuntu:20.04
RUN apt-get update -y
RUN apt-get install -y python3 bash-completion
RUN apt-get update && apt-get install -y git g++ python3-pip curl sudo unzip
RUN pip install --upgrade pip

COPY web/requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

RUN pip install -r requirements.txt

# installing gcloud
RUN curl -sSL https://sdk.cloud.google.com | bash

COPY . /app
COPY web/static /app/static
COPY web/main.py /app
COPY web/deployment.py /app
COPY web/templates /app/templates
COPY web/mongo_handler /app/mongo_handler
COPY web/mongo_boot_dump /app/mongo_boot_dump
COPY web/variables /app/variables
COPY web/trolley_small.png /app

ADD web/scripts/az_caching_script.py az_caching_script.py
ADD web/scripts/gcp_caching_script.py gcp_caching_script.py
ADD web/scripts/aws_caching_script.py aws_caching_script.py
ADD web/scripts/aws_discovery_script.py aws_discovery_script.py
ADD web/scripts/az_discovery_script.py az_discovery_script.py
ADD web/scripts/gcp_discovery_script.py gcp_discovery_script.py
RUN chmod +x trolley_api.sh az_cache.sh aws_cache.sh gcp_cache.sh aws_discovery.sh az_discovery.sh gcp_discovery.sh

CMD ./trolley_api.sh
#ENTRYPOINT ["tail", "-f", "/dev/null"]
# Command to execute to run the Google App run
#CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app

#ENTRYPOINT ["tail", "-f", "/dev/null"]