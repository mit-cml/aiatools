#!/usr/bin/env python

from setuptools import setup, find_packages
from aiatools import __version__

with open('README.md') as f:
    long_description = f.read()

setup(name='aiatools',
      version=__version__,
      description='Tools for extracting information from App Inventor AIA files',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Evan W. Patton',
      author_email='ewpatton@mit.edu',
      url='https://github.com/mit-cml/aiatools',
      packages=find_packages(),
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Intended Audience :: Education',
          'Intended Audience :: Science/Research',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Natural Language :: English',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Topic :: Education',
          'Topic :: Scientific/Engineering :: Information Analysis',
          'Topic :: Software Development',
          'Topic :: Utilities'
      ],
      license='GPLv3+',
      keywords='App Inventor AIA extraction analysis toolkit',
      entry_points={
          'console_scripts': [
              'aia = aiatools:aia_main'
          ]
      },
      install_requires=[
          'jprops>=2.0.2'
      ],
      package_data={
          'aiatools': ['simple_components.json']
      }
      )
