FROM python:alpine

RUN apk update && apk --no-cache add  \
    build-base

RUN mkdir /app

COPY requirements.txt /app

WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt

RUN addgroup jeopardy_group && adduser -D -G jeopardy_group -s /bin/bash jeopardy_user

COPY . /app

RUN chown -R jeopardy_user:jeopardy_group /app
USER jeopardy_user

EXPOSE 5000

ENTRYPOINT ["./gunicorn.sh"]