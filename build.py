import PyInstaller.__main__
import os

if __name__ == "__main__":
    PyInstaller.__main__.run([
        'tuneterm/__main__.py',
        '--name=TuneTerm',
        '--onefile',
        '--console',
        '--clean'
    ])
