FROM python:3
ENV PYTHONUNBUFFERED 1

RUN mkdir /code
WORKDIR /code
ADD requirements.txt /code/
RUN pip install -r requirements.txt
ADD . /code/

CMD python3 main.py 'http://www.azuolynogimnazija.lt/uploads/tvark/tvark17-18_2p/index.htm'