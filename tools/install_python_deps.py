#!/usr/bin/env python

import subprocess
import os
from os.path import join as pjoin

for dep in open(pjoin(os.path.dirname(__file__), '../requirements.txt')):
    if 'cesium' in dep and 'dev' in dep:
        try:
            import cesium
            wanted_version = dep.split('=')[-1].strip()
            if cesium.__version__ == wanted_version:
                break
        except ImportError:
            pass

        subprocess.call(['pip', 'uninstall', '-y', 'cesium'])
        subprocess.call(['pip', 'install',
                         'git+git://github.com/cesium-ml/cesium#egg=cesium'])

subprocess.call(['pip', 'install', '-r', 'requirements.txt'])

