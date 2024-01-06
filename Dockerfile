# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster
WORKDIR /app
RUN pip3 install requests rich


CMD ["python3", "signal_spot_bot.py"]
