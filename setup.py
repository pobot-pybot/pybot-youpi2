from setuptools import setup, find_packages
from git_version import git_version

setup(
    name='pybot-youpi2',
    version=git_version(),
    namespace_packages=['pybot'],
    packages=find_packages("src"),
    package_dir={'': 'src'},
    url='',
    license='',
    author='Eric Pascual',
    author_email='eric@pobot.org',
    install_requires=['pybot-dspin', 'pybot-lcd'],
    download_url='https://github.com/Pobot/PyBot',
    description='Library for Youpi arm controlled by STMicro L6470 (aka dSPIN)',
    entry_points={
        'console_scripts': [
            'youpi2-demo = pybot.youpi2.demo:main',
            'youpi2-ctrl = pybot.youpi2.control_panel:main'
        ]
    }
)
