FROM python:3-slim

RUN apt-get update

COPY requirements.txt /
COPY {SAMPLE}.py /
COPY c8y_api /c8y_api

RUN pip install -r requirements.txt


ENTRYPOINT ["python", "-u", "/{SAMPLE}.py"]
