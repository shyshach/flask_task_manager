FROM python:3.6-slim

COPY . /flask_servers

WORKDIR /flask_servers

RUN pip install -r requirements.txt