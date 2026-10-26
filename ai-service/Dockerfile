# AI service image. Standard library only, so no pip install step is needed.
FROM python:3.12-slim
WORKDIR /app
COPY ai-service/aiservice ./aiservice
ENV AI_SERVICE_PORT=8081
ENV BANKING_BASE_URL=http://banking:8080
EXPOSE 8081
CMD ["python", "-m", "aiservice.server"]
