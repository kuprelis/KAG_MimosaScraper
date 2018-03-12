FROM python:3-alpine
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD . /code/
RUN apk add --update --no-cache gcc g++ libxslt-dev \
&& pip install -r requirements.txt

CMD python3 main.py