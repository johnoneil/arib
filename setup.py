# vim: set ts=2 expandtab:
from setuptools import setup

#version 0.1: Initial version
#version 0.2: Added simple parsing of .ts files
#version 0.3: Added ts2ass tool

def readme():
  with open('README.md') as f:
    return f.read()

def requirements():
  with open('requirements.txt') as f:
    return f.read().splitlines()

setup(name='arib',
  version='0.3',
  description='Japan Association of Radio Industries and Businesses (ARIB) MPEG2 Transport Stream Closed Caption Decoding Tools',
  long_description = readme(),
	classifiers=[
    'Development Status :: 3 - Alpha',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 2.7',
    'Topic :: Multimedia :: Sound/Audio :: Conversion',
  ],
  keywords = 'Japanese Closed Caption arib b-24 MPEG TS PES',
  url='https://github.com/johnoneil/arib',
  author='John O\'Neil',
  author_email='oneil.john@gmail.com',
  license='MIT',
  packages=[
    'arib',
  ],
  install_requires = requirements(),
  entry_points = {
    'console_scripts': [
      'ts2ass=arib.ts2ass:main',
  ],
  },
  zip_safe=True)
