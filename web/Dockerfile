FROM ubuntu:20.04
RUN apt-get update -y
RUN apt-get install -y python3
RUN apt-get update && apt-get install -y git g++ python3-pip curl net-tools mongodb
RUN pip install --upgrade pip

COPY ./requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app
COPY static /app/static
COPY main.py /app
COPY templates /app/templates
COPY mongo_handler /app/mongo_handler
COPY variables /app/variables

ADD ../trolley_api.sh /trolley_api.sh
ADD ../gke_cache.sh /gke_cache.sh
RUN chmod +x trolley_api.sh gke_cache.sh
#CMD ["python3",  "main.py" ]