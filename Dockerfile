FROM python:3-alpine
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN pip install -r requirements.txt

CMD python3 main.py