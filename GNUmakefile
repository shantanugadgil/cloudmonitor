
TAG ?= "vLATEST"

build:
	DOCKER_BUILDKIT=1 docker image build --squash -t cloudmonitor:$(TAG) .

run:
	docker run -d -v /data:/data --name cm1 cloudmonitor:$(TAG)
	sleep 3
	docker ps

logs:
	docker logs cm1

clean:
	docker rm -f cm1
