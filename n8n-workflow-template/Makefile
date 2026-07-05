.PHONY: install demo run docker docker-clean

install:
	pip install -r requirements.txt

demo:
	python demo.py

run:
	python main.py || python bot.py || python scraper.py

docker:
	docker build -t $(shell basename $(CURDIR)) .
	docker run --rm --env-file .env $(shell basename $(CURDIR))

docker-clean:
	docker rmi $(shell basename $(CURDIR)) 2>/dev/null || true
