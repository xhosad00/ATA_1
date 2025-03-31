test:
	python3 -m unittest tests/test_cartctl.py -b

cov:
	coverage run --branch -m unittest tests/test_cartctl.py
	coverage report -m
	coverage html

verb:
	python3 -m unittest tests/test_cartctl.py -v

factory: cartctl/jarvis.png

.SUFFIXES: .png .dot

.dot.png:
	dot -Tpng -o $@ $<

cartctl/jarvis.dot: cartctl/jarvisenv.py
	python -c 'from cartctl import jarvisenv; jarvisenv.Jarvis.TRACKS.export("cartctl/jarvis.dot")'
