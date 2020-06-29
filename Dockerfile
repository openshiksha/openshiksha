FROM python:2.7.18-buster

# install nginx
RUN apt-get update && apt-get -y install nginx=1.14*

# Env vars
ENV WORKDIR /usr/src/app
ENV PYTHONUNBUFFERED 1
ENV OPENSHIKSHA_ENV PROD

WORKDIR ${WORKDIR}

COPY . .

# Setup nginx conf
RUN devops/compile-nginx.sh
RUN echo "include ${WORKDIR}/devops/nginx.compiled.conf;" > /etc/nginx/nginx.conf

RUN pip install --no-cache-dir -r pip-requirements.txt

EXPOSE 9878

ENTRYPOINT [ "devops/run-production-server.sh" ]