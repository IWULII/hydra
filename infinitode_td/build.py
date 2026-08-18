#!/usr/bin/env python3
"""
Build script to create Windows executable
Run this on Windows to create the .exe file
"""

import PyInstaller.__main__
import os
import shutil

# Clean previous builds
if os.path.exists('dist'):
    shutil.rmtree('dist')
if os.path.exists('build'):
    shutil.rmtree('build')
if os.path.exists('infinitode_td.spec'):
    os.remove('infinitode_td.spec')

PyInstaller.__main__.run([
    'main.py',
    '--name=InfinitodeTD',
    '--onefile',
    '--windowed',
    '--icon=NONE',
    '--add-data=config:config',
    '--hidden-import=numpy',
    '--hidden-import=pygame',
])

print("\n" + "="*50)
print("Build complete!")
print("Executable located at: dist/InfinitodeTD.exe")
print("="*50)
