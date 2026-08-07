.PHONY: load validate ratios screener valuation nlp cashflow reports dashboard api test clean all

load:
	python3 src/etl/loader.py

validate:
	python3 src/etl/validator.py

ratios:
	python3 src/analytics/populate_ratios.py

screener:
	python3 src/screener/export_screener.py
	python3 src/analytics/peer.py
	python3 src/analytics/export_peer_comparison.py
	python3 src/analytics/radar.py

valuation:
	python3 src/analytics/valuation.py

nlp:
	python3 src/nlp/parser.py
	python3 src/nlp/pros_cons_generator.py

cashflow:
	python3 src/analytics/cashflow_intelligence_report.py

reports:
	python3 src/reports/tearsheet.py
	python3 src/reports/sector_report.py
	python3 src/reports/portfolio_summary.py

dashboard:
	streamlit run src/dashboard/app.py

api:
	@echo "No standalone API server in this build -- data is served directly from nifty100.db by the dashboard."

test:
	python3 tests/run_tests.py tests/etl tests/kpi

clean:
	rm -f db/nifty100.db
	rm -rf output/*.csv output/*.xlsx output/*.log output/*.md
	rm -rf reports/tearsheets/* reports/sector/* reports/portfolio/* reports/radar_charts/*

all: load validate ratios screener valuation nlp cashflow reports test
