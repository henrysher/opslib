#!/bin/sh
export PYTHONPATH=`pwd`
nosetests -s -v --with-coverage --cover-package=opslib --cover-html  unit
