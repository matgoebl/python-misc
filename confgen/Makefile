APP=confgen.py
PYTHON_MODULES=click PyYAML ruamel.yaml pyhocon
VENV=.venv

all: install

requirements.txt:
	python3 -m pip install --user virtualenv
	python3 -m virtualenv $(VENV) && . $(VENV)/bin/activate && python3 -m pip install --upgrade pip && python3 -m pip install $(PYTHON_MODULES)
	. $(VENV)/bin/activate && python3 -m pip freeze --all | grep -v pkg_resources==0.0.0 > requirements.txt

$(VENV): requirements.txt
	python3 -m pip install --user virtualenv
	python3 -m virtualenv $(VENV) && . $(VENV)/bin/activate && python3 -m pip install -r requirements.txt
	touch $(VENV)

venv: $(VENV)

roundtrip_yaml:
	. $(VENV)/bin/activate && \
	 ./$(APP) -i empty.yaml yamllist -i hostlist.yaml -o out.yaml --mode add && \
	 diff -u hostlist.yaml out.yaml

#empty.yaml

test_yaml: venv
	. $(VENV)/bin/activate && \
	 for mode in merge replace add delete filter; do \
	 ./$(APP) -i change.yaml yamllist -i hostlist.yaml -o out.$$mode.yaml --mode $$mode; \
	 diff -u test.$$mode.yaml out.$$mode.yaml || echo 'TEST FAILED'; \
	done

test_hocon: venv
	. $(VENV)/bin/activate && python3 ./$(APP) -i change.yaml -vv hoconlist -i tree.conf -o out.conf

clean:
	rm -rf $(VENV)
	find -iname "*.pyc" -delete 2>/dev/null || true
	find -name __pycache__ -type d -exec rm -rf '{}' ';' 2>/dev/null || true

distclean: clean
	rm -rf requirements.txt

install:

.PHONY: all clean distclean install
