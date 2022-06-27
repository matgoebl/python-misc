APP=confgen.py
PYTHON_MODULES=click PyYAML ruamel.yaml
VENV=.venv

all: install

requirements.txt:
	python3 -m pip install --user virtualenv
	python3 -m virtualenv $(VENV) && . $(VENV)/bin/activate && python3 -m pip install --upgrade pip && python3 -m pip install $(PYTHON_MODULES)
	. $(VENV)/bin/activate && python3 -m pip freeze --all | grep -v pkg_resources==0.0.0 > requirements.txt

$(VENV): requirements.txt
	python3 -m pip install --user virtualenv
	python3 -m virtualenv $(VENV) && . $(VENV)/bin/activate && python3 -m pip install -r requirements.txt
	touch $(VENV)/.stamp

$(VENV)/.stamp: $(VENV)

venv-setup: $(VENV)/.stamp

run: $(VENV)/.stamp
	#. $(VENV)/bin/activate && python3 ./$(APP)
	cp -f hostlist.yaml test.yaml; ./confgen.py -i change.yaml -vv baselist -o test.yaml

clean:
	rm -rf $(VENV)
	find -iname "*.pyc" -delete 2>/dev/null || true
	find -name __pycache__ -type d -exec rm -rf '{}' ';' 2>/dev/null || true

distclean: clean
	rm -rf requirements.txt

install:

.PHONY: all venv-setup run clean distclean install
