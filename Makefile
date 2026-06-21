.PHONY: build serve migrate deps

deps:
	python3 -m pip install --quiet markdown

build: deps
	python3 build.py

serve: build
	@echo "Serving at http://localhost:8000 (Ctrl+C to stop)"
	python3 -m http.server 8000

migrate: deps
	python3 migrate.py
