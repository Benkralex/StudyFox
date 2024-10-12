FROM python:3.8-slim
WORKDIR /app

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt
COPY ./src /app

RUN chmod +x /app/gunicorn.sh

EXPOSE 8000

CMD ["bash", "gunicorn.sh"]