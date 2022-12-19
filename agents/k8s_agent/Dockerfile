FROM ubuntu:20.04
RUN apt-get update -y
RUN apt-get install -y python3
RUN apt-get update && apt-get install -y git g++ python3-pip curl
RUN pip install --upgrade pip

COPY agents/k8s_agent/requirements.txt /app/requirements.txt

# switch working directory
WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app
COPY agents/k8s_agent/main.py /app
COPY web/variables /app/variables


CMD ["python3",  "main.py" ]