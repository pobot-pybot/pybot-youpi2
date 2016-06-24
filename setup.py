from setuptools import setup, find_packages

setup(
    name='pybot-youpi2',
    setup_requires=['setuptools_scm'],
    use_scm_version={
        'write_to': 'src/pybot/youpi2/__version__.py'
    },
    namespace_packages=['pybot'],
    packages=find_packages("src"),
    package_dir={'': 'src'},
    url='',
    license='',
    author='Eric Pascual',
    author_email='eric@pobot.org',
    install_requires=['pybot-dspin', 'pybot-lcd>=0.11.0'],
    download_url='https://github.com/Pobot/PyBot',
    description='Library for Youpi arm controlled by STMicro L6470 (aka dSPIN)',
    entry_points={
        'console_scripts': [
            'youpi2-demo = pybot.youpi2.demo:main',
            'youpi2-ctrl = pybot.youpi2.toplevel:main'
        ]
    }
)
