.PHONY: demo test clean
demo:
	python demo.py
test:
	python -m pytest tests/ -v
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
