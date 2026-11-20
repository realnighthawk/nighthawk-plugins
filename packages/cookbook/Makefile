.PHONY: check stage

stage:
	node bin/stage-skills.mjs

check: stage
	python3 tools/lint.py
	python3 -m pytest -q
