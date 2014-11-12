#!/usr/bin/env python

from distutils.core import setup

setup(name='cql-migrate',
	version='0.1',
	author='Phil Wise',
	author_email='phil@advancedtelematic.com',
	url='https://gitlab.advancedtelematic.com/ats_dev/cql-migrate',
	packages=['cqlmigrate'],
	scripts=['bin/cql-migrate'])
