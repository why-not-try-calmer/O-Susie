FROM python:3.10

EXPOSE 80

RUN mkdir /opt/app
WORKDIR /opt/app

COPY ./requirements.txt /opt/app
RUN pip install -r requirements.txt --upgrade pip

COPY . /opt/app
CMD ["python3", "bot.py", "--webhook"]