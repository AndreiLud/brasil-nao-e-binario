# Convenience targets. Everything runs through run_all.py.
PY ?= .venv/bin/python

.PHONY: all setup data site serve screenshots test clean

setup:
	python3 -m venv .venv && $(PY) -m pip install -r requirements.txt

all:
	$(PY) run_all.py

data:
	$(PY) run_all.py --skip-notebook

site:
	$(PY) -m src.render

serve:
	cd docs && python3 -m http.server 8000

screenshots:
	$(PY) -m src.screenshots og

test:
	$(PY) -m src.smoke

clean:
	rm -rf data/interim data/processed
