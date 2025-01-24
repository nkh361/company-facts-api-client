FROM python:3.8-slim

# environment variables
ENV PYTHONBUFFERED=1 \
  FLASK_APP=server/app.py \
  FLASK_ENV=production

# set the working directory inside container
WORKDIR /app

# copy requirements file
COPY requirements.txt /app/

# install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# copy the application code
COPY . /app/

# port for flask
EXPOSE 5000

# command to run the flask app
CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
