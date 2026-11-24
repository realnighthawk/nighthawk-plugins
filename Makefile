.PHONY: check

check:
	python3 scripts/sync-shared.py --check
	sh plugins/mission-control/scripts/test-hooks.sh
	cd packages/mission-control && node bin/stage.mjs && npm test >/dev/null
