#!/usr/bin/env python

from distutils.core import setup

setup(name='cfn_lambda_extractor',
      version='0.1.0',
      description='Extract embeded AWS Lambda functions from Cloudformation templates.',
      author='Brett Weaver',
      author_email='brett_weaver@intuit.com',
      packages=['cfn_lambda_extractor'],
      url='https://github.intuit.com/bw-intuit/cfn_lambda_extractor',
      entry_points = {
          'console_scripts': [
              'cfn_lambda_extractor = cfn_lambda_extractor.cli:run'
              ]
          }
     )
