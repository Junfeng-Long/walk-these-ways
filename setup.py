from setuptools import find_packages
from distutils.core import setup

setup(
    name='a1_gym',
    version='1.0.0',
    author='Gabriel Margolis',
    license="BSD-3-Clause",
    packages=find_packages(),
    author_email='gmargo@mit.edu',
    description='Toolkit for deployment of sim-to-real RL on the Unitree A1.',
    install_requires=['ml_logger==0.8.71',
                      'ml_dash==0.3.20',
                      'jaynes==0.8.11',
                      'params-proto==2.9.6',
                      'gym',
                      'tqdm',
                      'matplotlib',
                      ]
)
