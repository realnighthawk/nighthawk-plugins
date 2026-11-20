.PHONY: check

check:
	python3 scripts/sync-shared.py --check
	$(MAKE) -C packages/cookbook check
	sh plugins/mission-control/scripts/test-hooks.sh
