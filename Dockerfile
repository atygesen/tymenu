FROM python:3.11-alpine

EXPOSE 5000
WORKDIR /app

COPY ./mysql_deploy_requirements.txt .

RUN apk update \
    && apk add --virtual build-deps gcc musl-dev \
    && apk add --no-cache mariadb-dev && \
    pip install --upgrade pip && \
    pip install -r mysql_deploy_requirements.txt && \
    pip cache purge && \
    apk del build-deps

COPY . /app

RUN pip install -e .

CMD ["flask", "run", "--host", "0.0.0.0"]
