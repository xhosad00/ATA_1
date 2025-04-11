test:
	python3 -m unittest tests/test_cartctl.py -b

cov:
	coverage run --branch -m unittest tests/test_cartctl.py
	coverage report -m
	coverage html

verb:
	python3 -m unittest tests/test_cartctl.py -v

#example: make single t=cart_props
single:
	python3 -m unittest tests.test_cartctl.TestCartRequests.test_$(t) -v 

factory: cartctl/jarvis.png

.SUFFIXES: .png .dot

.dot.png:
	dot -Tpng -o $@ $<

allDiagrams:
	for file in diagrams/*.dot; do \
		dot -Tpng -o "$${file%.dot}.png" "$$file"; \
	done

cartctl/jarvis.dot: cartctl/jarvisenv.py
	python -c 'from cartctl import jarvisenv; jarvisenv.Jarvis.TRACKS.export("cartctl/jarvis.dot")'

# need to create tmp folder due to folder naming (cartclt/cartctl..)
zip:
	mkdir -p cartctl_tmp/cartctl
	cp -r Makefile README.md diagrams tests cartctl_tmp/cartctl/
	cp -r cartctl cartctl_tmp/cartctl/cartctl_src
	cd cartctl_tmp && zip -r ../xhosad00.zip cartctl
	rm -rf cartctl_tmp