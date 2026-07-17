.PHONY: install load validate test clean

install:
	pip install -r requirements.txt

load:
	python src/etl/loader.py

validate:
	python src/etl/validator.py

test:
	python -m pytest tests/ -v

clean:
	rm -f db/nifty100.db
	rm -f output/*.csv
	find . -type d -name __pycache__ -exec rm -rf {} +
