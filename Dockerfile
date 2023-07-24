FROM python:3.11

WORKDIR /app

RUN pip install --upgrade pip
COPY ./mysql_requirements.txt ./requirements.txt ./
RUN pip install \
    -r requirements.txt \
    -r mysql_requirements.txt

COPY . /app

RUN pip install -e .

CMD ["flask", "run", "--host", "0.0.0.0"]
