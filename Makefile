.PHONY: demo test

demo:
	python3 -m horvessane examples/incident.json

test:
	python3 -m unittest discover -s tests -v
