FROM ubuntu:latest
LABEL authors="vrauch"
# Step 1: Use a lightweight Python image as the base
FROM python:3.9-slim

# Step 2: Set the working directory in the container
WORKDIR /app

# Step 3: Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Step 4: Copy the rest of the application files
COPY . .

# Step 5: Specify the default command to run the app
CMD ["python", "MainMenu.py"]
ENTRYPOINT ["top", "-b"]