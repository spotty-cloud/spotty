#!/usr/bin/env python

from setuptools import setup, find_packages


setup(name='spotty',
      version='1.0.2',
      description='Train deep learning models on AWS EC2 Spot Instances',
      url='http://github.com/apls777/spotty',
      author='Oleg Polosin',
      author_email='apls777@gmail.com',
      license='MIT',
      packages=find_packages(exclude=['tests*']),
      package_data={'spotty': ['data/create_ami.yaml', 'data/run_container.yaml']},
      scripts=['bin/spotty'],
      install_requires=[
          'botocore>=1.10.0',
          'boto3>=1.7.0',
          'cfn_tools',
          'schema',
      ],
      classifiers=[
          'Development Status :: 3 - Alpha',
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
