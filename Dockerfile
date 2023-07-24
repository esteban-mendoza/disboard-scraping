FROM python:3.8-slim-bullseye

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV SPIDER_NAME=servers
ENV LANGUAGE=""
ENV USE_WEB_CACHE=False
ENV FOLLOW_PAGINATION_LINKS=True
ENV FOLLOW_CATEGORY_LINKS=True
ENV FOLLOW_TAG_LINKS=True


