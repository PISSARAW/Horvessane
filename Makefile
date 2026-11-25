.PHONY: demo test demo-suite test-suite

demo-suite:
	python3 integration/run.py

test-suite:
	python3 integration/test_pipeline.py

demo:
	python3 -m horvessane examples/incident.json

test:
	python3 -m unittest discover -s tests -v
