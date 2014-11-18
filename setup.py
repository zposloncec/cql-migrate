#!/usr/bin/env python

# Copyright 2014 ATS Advanced Telematic Systems GmbH
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from distutils.core import setup

setup(name='cql-migrate',
    version='0.1',
    author='Phil Wise',
    author_email='phil@advancedtelematic.com',
    url='https://gitlab.advancedtelematic.com/ats_dev/cql-migrate',
    packages=['cqlmigrate'],
    scripts=['bin/cql-migrate'])
# vim: set expandtab tabstop=4 shiftwidth=4:
