FROM python:3.9-slim-bullseye

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config && \
    rm -rf /var/lib/apt/lists/*

COPY ./mysql_requirements.txt ./requirements.txt ./
RUN pip install --no-cache-dir \
    -r requirements.txt \
    -r mysql_requirements.txt

COPY . /app

RUN pip install --no-cache-dir -e .

RUN chmod u+x ./entrypoint.sh

ENTRYPOINT [ "./entrypoint.sh" ]
