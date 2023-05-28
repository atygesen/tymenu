FROM python:3.11

COPY . /app

WORKDIR /app

RUN pip install -e .[mysql]

CMD ["flask", "run", "--host", "0.0.0.0"]
