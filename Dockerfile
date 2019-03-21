FROM ubuntu:16.04

RUN apt-get update && apt-get install -y \
    python3 python3-dev build-essential python3-pip libssl-dev gcc\
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoclean

COPY ./req_linux.txt /tmp/
RUN pip3 install -r /tmp/req_linux.txt --no-cache-dir --disable-pip-version-check -i https://pypi.douban.com/simple/ \
    && rm -rf /tmp/req_linux.txt

ENV TZ=Asia/Shanghai

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

WORKDIR /jikescrapy

CMD ["scrapy", "--version"]