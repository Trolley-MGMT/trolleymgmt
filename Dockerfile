FROM ubuntu:20.04
RUN apt-get update -y
RUN apt-get install -y python3
RUN apt-get update && apt-get install -y git g++ python3-pip curl sudo unzip
RUN pip install --upgrade pip

COPY web/requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app
COPY web/static /app/static
COPY web/main.py /app
COPY web/templates /app/templates
COPY web/mongo_handler /app/mongo_handler
COPY web/variables /app/variables
COPY web/trolley_small.png /app

ADD web/scripts/aks_caching_script.py aks_caching_script.py
ADD web/scripts/gke_caching_script.py gke_caching_script.py
ADD web/scripts/eks_caching_script.py eks_caching_script.py
ADD web/scripts/aws_discovery_script.py aws_discovery_script.py
RUN chmod +x trolley_api.sh aks_cache.sh gke_cache.sh eks_cache.sh aws_discovery.sh

CMD ./trolley_api.sh
#ENTRYPOINT ["tail", "-f", "/dev/null"]