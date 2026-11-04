.PHONY: test demo-replay start-service audit verify receipt reset-baseline

PYTHON ?= python3

test:
	$(PYTHON) -m pytest checkout-service/test_service.py finops-hq/test_finops.py -v

demo-replay:
	$(PYTHON) scripts/demo_replay.py

start-service:
	$(PYTHON) checkout-service/app.py --port 8090

audit:
	$(PYTHON) finops-hq/probe.py audit --url http://127.0.0.1:8090

verify:
	$(PYTHON) finops-hq/probe.py verify --url http://127.0.0.1:8090

receipt:
	$(PYTHON) finops-hq/probe.py mint-receipt --url http://127.0.0.1:8090

reset-baseline:
	$(PYTHON) checkout-service/service_config.py baseline

