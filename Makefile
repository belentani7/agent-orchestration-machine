PYTHONPATH=src

run-demo:
	PYTHONPATH=$(PYTHONPATH) python3 -m machine --demo

run-health:
	PYTHONPATH=$(PYTHONPATH) python3 -m machine --health

test:
	PYTHONPATH=$(PYTHONPATH) python3 -m unittest discover -s tests -v
