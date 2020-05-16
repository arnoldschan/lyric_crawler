FROM python:slim
COPY ./requirements.txt /usr/app/
WORKDIR /usr/app
RUN pip install -r requirements.txt
COPY ./crawlers /usr/app/crawlers
COPY ./main.py /usr/app/
CMD ["python","main.py"]