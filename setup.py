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


setup(name='spotty',
      version=get_version(),
      description='Train deep learning models on AWS EC2 Spot Instances',
      url='http://github.com/apls777/spotty',
      author='Oleg Polosin',
      author_email='apls777@gmail.com',
      license='MIT',
      packages=find_packages(exclude=['tests*']),
      package_data={'spotty': [
          'data/create_ami.yaml',
          'data/run_container.yaml',
          'data/create_instance_profile.yaml',
      ]},
      scripts=['bin/spotty'],
      install_requires=[
          'botocore>=1.10.0',
          'boto3>=1.7.0',
          'cfn_flip',
          'schema',
      ],
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Science/Research',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'Natural Language :: English',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
      ])
