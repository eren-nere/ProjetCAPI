FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get remove -y build-essential && apt-get autoremove -y

COPY . /app/

RUN python3 manage.py collectstatic --noinput

EXPOSE 8000

ENV dockerenable=true

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
