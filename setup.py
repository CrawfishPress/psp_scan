#!/usr/bin/env python
from __future__ import print_function
from setuptools import setup

import sys

setup_args = dict(
    name='psp_scan',
    version='0.9',
    author='John Crawford',
    author_email='psp_dev@crawfishpress.com',
    url='https://github.com/Crawfishpress/psp_scan',
    description='Python package for working with Paintshop Pro files',
    license='MIT License',
    zip_safe=False,
    keywords="paintshoppro psp imaging conversion pil pillow",
    long_description = open('README.rst').read() + "\n\n" + open('CHANGES.rst').read(),

    install_requires=['Pillow>=3.3.0'],
    packages=['psp_scan'],
    package_dir={'psp_scan': 'src'},

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: Microsoft :: Windows :: Windows 7',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2 :: Only',
        'Programming Language :: Python :: 2.7',
        'Topic :: Multimedia :: Graphics',
        'Topic :: Multimedia :: Graphics :: Graphics Conversion',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)


def main():
    try:
        setup(**setup_args)
    except Exception as _:
        msg = "Couldn't install package {0}...".format(setup_args['name'])
        print (msg)
        sys.exit(1)

if __name__ == '__main__':
    main()
