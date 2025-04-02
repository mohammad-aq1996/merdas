FROM python:3.12.3

WORKDIR /app

COPY requirements.txt /app/
RUN pip install -r requirements.txt

COPY . /app/

#COPY entrypoint.sh /app/entrypoint.sh
#
#RUN chmod +x /app/entrypoint.sh
#
#ENTRYPOINT ["sh", "/app/entrypoint.sh"]

EXPOSE 8005

