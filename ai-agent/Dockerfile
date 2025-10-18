FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY agent.py .
COPY english_teacher_prompt.py .

# Create a non-root user
RUN useradd -m -u 1000 agent && chown -R agent:agent /app
USER agent

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the agent using LiveKit CLI dev mode (for persistent worker)
CMD ["python", "agent.py", "dev"]
