
TAG ?= "vLATEST"
OTHER_IMAGE ?= "nosuchrepo/cloudmonitor"

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

retag: build
	# OTHER_IMAGE=private.repo.tld/cloudmonitor
	docker tag cloudmonitor:$(TAG) $(OTHER_IMAGE):$(TAG)
	docker push $(OTHER_IMAGE):$(TAG)
