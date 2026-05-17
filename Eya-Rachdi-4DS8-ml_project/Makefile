.PHONY: all install prepare train evaluate save run-api build push run clean

# ----------- Pipeline complet -----------
all: install prepare train save evaluate

install:
	pip install -r requirements.txt

prepare:
	python main.py --prepare

train:
	python main.py --train

evaluate:
	python main.py --evaluate

save:
	python main.py --save

# ----------- Lancement de l'API -----------
run-api:
	@echo "Lancement de l'API sur http://127.0.0.1:8000/docs"
	uvicorn app:app --reload

# ----------- Docker -----------
IMAGE_NAME = mon-image
TAG = latest
DOCKER_USER = ton_nom_utilisateur_docker

build:
	docker build -t $(IMAGE_NAME):$(TAG) .

push: build
	docker tag $(IMAGE_NAME):$(TAG) $(DOCKER_USER)/$(IMAGE_NAME):$(TAG)
	docker push $(DOCKER_USER)/$(IMAGE_NAME):$(TAG)

run: build
	docker rm -f $(IMAGE_NAME)_container || true
	docker run -d --name $(IMAGE_NAME)_container -p 8000:8000 $(IMAGE_NAME):$(TAG)

clean:
	docker rm -f $(IMAGE_NAME)_container || true
	docker rmi -f $(IMAGE_NAME):$(TAG) || true
