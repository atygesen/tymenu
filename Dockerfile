FROM python:3.11

COPY . /app

WORKDIR /app

RUN pip install -e .[mysql]

EXPOSE 5000
CMD ["flask", "run", "--host", "0.0.0.0"]
