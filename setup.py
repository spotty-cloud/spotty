#!/usr/bin/env python

from setuptools import setup

setup(name='spotty',
      version='1.0.0',
      description='Train models on AWS Spot Instances',
      url='http://github.com/apls777/spotty',
      author='Oleg Polosin',
      author_email='apls777@gmail.com',
      license='MIT',
      packages=['spotty', 'spotty.commands'],
      package_data={'spotty': ['data/launch-specification.json', 'data/unzip.py', 'data/user_data.sh']},
      scripts=['bin/spotty'],
      install_requires=[
          'botocore>=1.10.0',
          'boto3>=1.7.0',
          'yaml',
          'cfn_tools',
      ],
      classifiers=[
          'Development Status :: 3 - Alpha',
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
