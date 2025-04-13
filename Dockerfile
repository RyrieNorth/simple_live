FROM python:3.10-alpine
RUN mkdir /app
WORKDIR /app
COPY simple_live /app
RUN pip install -r /app/requirements.txt -i https://mirrors.ustc.edu.cn/pypi/simple
EXPOSE 5000
CMD ["python3", "/app/app.py"]
