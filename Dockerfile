FROM python:3.12.3-alpine
WORKDIR /app
COPY . .
RUN --mount=type=cache,id=custom-pip,target=/root/.cache/pip pip install -r requirements.txt

CMD ["python3", "main.py"]