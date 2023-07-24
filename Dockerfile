FROM python:3.11

EXPOSE 5000
WORKDIR /app

COPY . /app
RUN pip install -e .[mysql]

CMD ["flask", "run", "--host", "0.0.0.0"]
