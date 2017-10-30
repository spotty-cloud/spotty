#!/usr/bin/env python

from setuptools import setup

setup(name='cloud-training',
      version='0.1.0',
      description='Train models on AWS Spot Instances',
      url='http://github.com/apls777/cloud-training',
      author='Oleg Polosin',
      author_email='apls777@gmail.com',
      license='MIT',
      packages=['cloud_training', 'cloud_training.commands'],
      package_data={'cloud_training': ['data/launch-specification.json', 'data/unzip.py', 'data/user_data.sh']},
      scripts=['bin/cloud-training'],
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
