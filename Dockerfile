FROM python:3.11-alpine

WORKDIR /app

COPY triage.py .

ENTRYPOINT ["python", "triage.py"]
CMD ["./logs"]
