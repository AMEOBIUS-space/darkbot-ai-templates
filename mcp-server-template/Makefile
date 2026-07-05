.PHONY: run demo test docker clean

run:
	python src/server.py

demo:
	python demo.py

test:
	python -m pytest tests/ -v

docker:
	docker build -t mcp-server-template .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
