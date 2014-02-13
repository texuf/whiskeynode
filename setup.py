import os
import platform
from setuptools import setup



install_requires = ['mandrill']
if platform.python_version() < '2.7':
    install_requires.append('unittest2')

setup(
      name='whiskeynode',
      version='0.1',
      url='https://github.com/texuf/whiskeynode',
      classifiers = [
          'Programming Language :: Python :: 2.7',
          ],
      description='A graph ORM for MongoDB with a weak-reference cache.',
      license='Apache 2.0',
      author='Austin Ellis',
      author_email='austinellis@gmail.com',
      py_modules=['whiskeynode'],
      install_requires=['mongomock', 'pymongo'],
      scripts=[],
      namespace_packages=[]
      )
