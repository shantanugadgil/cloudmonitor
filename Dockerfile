FROM python:3-alpine

RUN apk update && apk add curl tzdata bash ca-certificates xz jq \
  && rm -rf /var/cache/apk/*

COPY requirements.txt .

RUN pip install --upgrade -r requirements.txt

COPY --chmod=0755 docker-entrypoint.bash /docker-entrypoint.bash

COPY --chmod=0755 html_gen.py /generate_html.py

COPY templates/ templates/

COPY html.tar.xz /html.tar.xz

ENTRYPOINT ["/docker-entrypoint.bash"]
