FROM python:3.12.3-slim

WORKDIR /app

 # copies the requirements file to the  docker container.
COPY requirement.txt .

RUN pip3 install --no-cache-dir -r requirement.txt

# copies the rest of the application code to the docker container.!
COPY . . 

 #available to all IP addresses.!(host is the variable name..)
ENV host="0.0.0.0"

# listing port .!!
EXPOSE 5000

CMD ["python", "app.py"]
