from setuptools import setup, find_packages
from setuptools.command.install import install

# from git_version import git_version


class PastInstallCommand(install):
    def run(self):
        super(PastInstallCommand, self).run()

setup(
    name='pybot-youpi2',
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
