PY ?= .venv/bin/python

all: fetch heatmap card

fetch:
	GITHUB_TOKEN=$${GITHUB_TOKEN:-$$(gh auth token)} $(PY) scripts/fetch_contributions.py
heatmap:
	$(PY) scripts/render_heatmap_svg.py
card:
	$(PY) scripts/make_info_card.py
photo:
	$(PY) scripts/prep_photo.py
	$(PY) scripts/make_ascii_svg.py
ascii:
	$(PY) scripts/make_ascii_svg.py

.PHONY: all fetch heatmap card photo ascii
