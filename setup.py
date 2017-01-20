# vim: set ts=2 expandtab:
from setuptools import setup

#version 0.1: Initial version
#version 0.2: Added simple parsing of .ts files
#version 0.3: Added ts2ass tool
#version 0.4: Added autosub tool
#version 0.5: Improved ts2ass tool
#version 0.55: Removed autosub tool, automated PID handling
#version 0.56: Better file writing and messages.
#version 0.57: Fixes for issues 13, 14
#version 0.58: fix for vertical position in some cases
#version 0.6.1: Performance improvements
#version 0.6.2: Numerous fixes and initial DRCS parsing

def readme():
  with open('README.md') as f:
    return f.read()

def requirements():
  with open('requirements.txt') as f:
    return f.read().splitlines()

setup(name='arib',
  version='0.6.2',
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
      'arib-ts2ass=arib.ts2ass:main',
      'arib-ts-extract=arib.ts_extract:main',
      'arib-es-extract=arib.es_extract:main',
  ],
  },
  zip_safe=True)
