FROM python:3.13-alpine
WORKDIR /code
COPY . .
RUN pip install -U pip
RUN pip install -r requirements.txt
CMD gunicorn main.wsgi -b 0.0.0.0:8000
