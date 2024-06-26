#!/usr/bin/env python3
#
# BSD 3-Clause License
#
# Copyright (c) 2022, ESnet
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Author: Ezra Kissel <kissel@es.net>
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

    with open("requirements.txt", "r") as fh:
        requirements = fh.read()

        setup(
            name='PolarizationControl',
            version='1.0',
            description='M-node Polarization Control Implementation',
            long_description=long_description,
            long_description_content_type="text/markdown",
            url='https://github.com/qlbnl/PolarizationControl',
            author='Ezra Kissel',
            classifiers=[
                'Development Status :: 5 - Production/Stable',
                'Intended Audience :: Developers',
                'Topic :: Software Development :: Libraries :: Application Frameworks',
                'License :: OSI Approved :: BSD License',
                'Programming Language :: Python :: 3',
            ],
            keywords='polarization light quantum',
            packages=find_packages(),
            setup_requires=requirements,
            install_requires=requirements,
            entry_points={
                'console_scripts': [
                    'pol_ctl = polctl.pol_ctl:main',
                ]
            }
        )
