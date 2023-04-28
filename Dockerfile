FROM mcr.microsoft.com/playwright:v1.32.0-jammy

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends python3-pip && apt-get clean

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

EXPOSE 8000

CMD [ "uvicorn", "server:app", "--host", "0.0.0.0" ]
