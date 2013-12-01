## Makefile for Ops Common Library ##
VERSION = ../../Common/build/TmVersion.h
BUILD = build/TmBuild.h

ifeq ($(wildcard ${VERSION}), ${VERSION})
        MAJOR_VERSION = $(shell grep TM_VERSION_SZ ${VERSION} | cut -d "\"" -f 2)
else
        MAJOR_VERSION = 0.0
endif
ifeq ($(wildcard ${VERSION}), ${VERSION})
        BUILD_VERSION = $(shell grep TM_BUILD_SZ ${BUILD} | cut -f3|tr -d " \"")
else
        BUILD_VERSION = 0000
endif

INSTALL_DIR = /opt/icsops/opslib
ROOT_DIR = $(abspath $(CURDIR)/)
SCRIPT_DIR = ${ROOT_DIR}
BUILD_ROOT = ${ROOT_DIR}/install
OUTPUT_DIR = ${ROOT_DIR}/output
EGG_DIR = ${ROOT_DIR}/egg
DOCS_DIR = ${OUTPUT_DIR}/docs
ICS_BUILD_DIR = ${BUILD_ROOT}${INSTALL_DIR}

.PHONY: all

all:	clean pkg

egg:	egg_clean \
	egg_pkg \
	egg_gen

pkg:	pkg_clean \
        pkg_dirs \
        pkg_scripts \
        pkg_tgz 

docs: docs_clean docs_dirs gen_docs

test: test_clean check

clean: egg_clean pkg_clean py_clean output_clean


## Packaging ##
egg_pkg:
	@mkdir -p ${EGG_DIR}/opslib
	@cp -a ${SCRIPT_DIR}/*.py ${EGG_DIR}/opslib
	@rm -f ${EGG_DIR}/opslib/setup.py
	@cp -a ${SCRIPT_DIR}/*.ini ${EGG_DIR}/opslib
	@cp -a ${SCRIPT_DIR}/setup.py ${EGG_DIR}
	@cp -ar ${SCRIPT_DIR}/icsutils ${EGG_DIR}/opslib

egg_gen:
	@cd ${EGG_DIR}; python setup.py bdist_egg
	@mkdir -p ${OUTPUT_DIR}
	@cp -a ${EGG_DIR}/dist/*.egg ${OUTPUT_DIR}

egg_clean:
	@rm -rf ${EGG_DIR}

pkg_dirs:
	@mkdir -p ${ICS_BUILD_DIR}
	@mkdir -p ${OUTPUT_DIR}

pkg_scripts:
	@cp -a ${SCRIPT_DIR}/*.py ${ICS_BUILD_DIR}
	@cp -a ${SCRIPT_DIR}/*.ini ${ICS_BUILD_DIR}
	@cp -ar ${SCRIPT_DIR}/icsutils ${ICS_BUILD_DIR}

pkg_tgz:
	@tar -cz --owner=root --group=root -C ${BUILD_ROOT} -f ${OUTPUT_DIR}/opscommon-${MAJOR_VERSION}.${BUILD_VERSION}.tgz .

pkg_clean:
	@rm -rf ${BUILD_ROOT}

## Document ##
docs_dirs:
	@mkdir -p ${DOCS_DIR}

gen_docs:
	$(MAKE) -C docs/ -f Makefile html
	@mv docs/_build/html ${DOCS_DIR}

docs_clean:
	$(MAKE) -C docs/ -f Makefile clean
	@rm -rf docs/_build
	@rm -rf docs/*.log
	@rm -rf ${DOCS_DIR}
	@rm -rf *.pyc

## Unit Test ##
check:
	$(MAKE) -C test/augeas check

test_clean:
	$(MAKE) -C test/augeas clean

## Clean Up ##
output_clean:  
	@rm -rf ${OUTPUT_DIR}

py_clean:
	@rm -fv *.pyc *.pyo
