FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .

# Create volume for settings persistence
VOLUME ["/app/data"]

# Expose port for health check
EXPOSE 8080

# Run bot
CMD ["python", "-u", "bot.py"]
