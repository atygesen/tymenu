FROM python:3.11

WORKDIR /app

COPY ./mysql_requirements.txt ./requirements.txt ./

# RUN apk update \
#     && apk add --virtual build-deps gcc musl-dev \
#     && apk add --no-cache mariadb-dev && \
#     pip install --upgrade pip && \
#     pip install -r mysql_deploy_requirements.txt && \
#     pip cache purge && \
#     apk del build-deps

# RUN apt update && \
#     apt install -y

RUN pip install --upgrade pip
RUN pip install \
    -r requirements.txt \
    -r mysql_requirements.txt

COPY . /app

RUN pip install -e .

CMD ["flask", "run", "--host", "0.0.0.0"]
