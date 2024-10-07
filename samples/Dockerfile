FROM python:3.10-slim

RUN apt-get update && apt-get -y upgrade

COPY requirements.txt /
COPY util.py /
COPY testing_util.py /
COPY {SAMPLE}.py /
COPY c8y_api /c8y_api
COPY c8y_tk /c8y_tk

RUN pip install --upgrade pip
RUN pip install -r requirements.txt


ENTRYPOINT ["python", "-u", "/{SAMPLE}.py"]
