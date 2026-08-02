.PHONY: install load validate ratios report dashboard test clean

install:
	pip install -r requirements.txt

load:
	python src/etl/loader.py

validate:
	python src/etl/validator.py

ratios:
	python src/analytics/populate_ratios.py

# Regenerates every derived output (peer percentiles, radar charts, capital
# allocation, ratio edge-case log, valuation, screener/peer Excel exports)
# in the correct dependency order - see run_pipeline.py's docstring for why
# order matters here (financial_ratios gets rebuilt from raw source data by
# loader.py, so anything reading it needs the full chain re-run afterward).
report:
	python run_pipeline.py

dashboard:
	streamlit run src/dashboard/app.py

test:
	python -m pytest tests/ -v

clean:
	rm -f db/nifty100.db
	rm -f output/*.csv
	find . -type d -name __pycache__ -exec rm -rf {} +

# NOTE: an 'api' target was listed in the Sprint 1 planning doc's summary,
# but no API epic/sprint has been scoped or built anywhere in Sprints 1-5 -
# there's no FastAPI/Flask app in this codebase to run. Left out rather
# than pointing at a script that doesn't exist; add this target if/when
# that work is actually scoped.
