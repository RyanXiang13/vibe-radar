# Use an official lightweight Python image
FROM python:3.10-slim

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /code

# Copy requirements first (to cache dependencies)
COPY requirements.txt /code/
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application code
COPY . /code/

# (Optional) Default command, though docker-compose overrides this
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]