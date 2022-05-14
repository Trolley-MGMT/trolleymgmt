
FROM python:3.8-alpine

RUN mkdir -p /templates


ADD config.ini /
ADD main.py /
ADD mongo_handler.py /
ADD mongo_objects.py /
ADD utils.py /
ADD variables.py /
ADD requirements.txt /
ADD templates/index.html /
ADD templates/login.html /
ADD templates/trigger_kubernetes_deployment.html /

COPY templates/ templates/

RUN pip install -r requirements.txt

CMD ["ls"]
CMD ["pwd"]

CMD ["python",  "main.py" ]