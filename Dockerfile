FROM python:3.11-slim-bullseye

WORKDIR /app

RUN pip install --upgrade pip && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config

COPY ./mysql_requirements.txt ./requirements.txt ./
RUN pip install \
    -r requirements.txt \
    -r mysql_requirements.txt

COPY . /app

RUN pip install -e .

CMD ["flask", "run", "--host", "0.0.0.0"]
