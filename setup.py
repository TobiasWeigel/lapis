from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='dkrz.digitalobjects',
      version=version,
      description="Digital Object Infrastructure",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Tobias Weigel',
      author_email='weigel@dkrz.de',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
