.PHONY: clean test accept rpm

NAME := exosphere
VERSION := $(shell python setup.py --version)
BUILD_NUMBER ?= 1
RELEASE_VER = $(BUILD_NUMBER)

VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/py.test
PEP8 := $(VENV)/bin/pep8
TOX := $(VENV)/bin/tox

PYSRC := $(shell find {$(NAME),test} -iname '*.py')
TARGET := $(PWD)/target


###############
# Boilerplate #
###############

default: test

clean:
	rm -rf .tox htmlcov .coverage .eggs results node_modules $(TARGET)

$(TARGET):
	mkdir -p $(TARGET)

test: $(TARGET)/test-output.xml


##############
# Virtualenv #
##############

$(VENV)/deps.touch: $(PIP) requirements.txt
	$(PIP) install -r requirements.txt
	touch $(VENV)/deps.touch

$(VENV)/bin/%: $(PIP)
	$(PIP) install $*

$(VENV)/bin/py.test: $(PIP)
	$(PIP) install pytest pytest-cov pytest-xdist pytest-django responses

$(PYTHON) $(PIP):
	virtualenv -p python3 venv
	$(PIP) install virtualenv


################
# Code Quality #
################

$(TARGET)/pep8.errors: $(TARGET) $(PEP8) $(PYSRC)
	$(PEP8) --exclude="venv" . | tee $(TARGET)/pep8.errors || true


################
# Unit Testing #
################

$(TARGET)/test-output.xml: $(PYSRC) tox.ini $(TARGET) $(PYTHON) $(VENV)/bin/py.test
	$(PYTHON) setup.py test
