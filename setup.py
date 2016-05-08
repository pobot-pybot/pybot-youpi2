from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools_scm import get_version

from textwrap import dedent


class CustomInstallCommand(install):
    def run(self):
        # create the version file
        with file('src/pybot/youpi2/__version__.py', 'w') as fp:
            fp.write(dedent('''
                # generated automatically by setup
                # DO NOT MODIFY
                version = "%s"
                ''').lstrip() % get_version())

        install.run(self)


setup(
    name='pybot-youpi2',
    cmdclass={
        'install': CustomInstallCommand
    },
    # version=git_version(),
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
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
            'youpi2-ctrl = pybot.youpi2.toplevel:main'
        ]
    }
)
