FROM python:3.8-slim

# Install dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 5500

CMD ["sh", "-c", "python app.py"]
