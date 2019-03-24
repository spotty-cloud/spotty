#!/usr/bin/env python

import os
import re
from setuptools import setup, find_packages


def get_version():
    root_dir = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(root_dir, 'spotty', '__init__.py')) as f:
        content = f.read()

    version_match = re.search(r'^__version__ = [\'"]([^\'"]*)[\'"]', content, re.M)
    if not version_match:
        raise RuntimeError('Unable to find version string.')

    return version_match.group(1)


def get_description():
    readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'README.md'))
    with open(readme_path, encoding='utf-8') as f:
        description = f.read()

    return description


setup(name='spotty',
      version=get_version(),
      description='Training deep learning models on AWS EC2 Spot Instances',
      url='http://github.com/apls777/spotty',
      author='Oleg Polosin',
      author_email='apls777@gmail.com',
      license='MIT',
      long_description=get_description(),
      long_description_content_type='text/markdown',
      packages=find_packages(exclude=['tests*']),
      package_data={'spotty.providers.aws.deployment.cf_templates': ['data/*.yaml']},
      scripts=['bin/spotty'],
      install_requires=[
          'boto3>=1.9.0',
          'cfn_flip',  # to work with CloudFormation templates
          'schema',
          'chevron',
      ],
      tests_require=['moto'],
      test_suite='tests',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'Natural Language :: English',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
      ])
