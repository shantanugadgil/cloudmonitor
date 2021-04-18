
build:
	DOCKER_BUILDKIT=1 docker image build -t cloudmonitor:v1 .

run:
	docker run -d -v /data:/data --name cm1 cloudmonitor:v1
	sleep 3
	docker ps

logs:
	docker logs cm1

clean:
	docker rm -f cm1
