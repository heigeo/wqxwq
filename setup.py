import os
from setuptools import setup

LONG_DESCRIPTION = """
WQX-compatible schema and HTML Mustache templates for use with the wq framework
"""


def parse_markdown_readme():
    """
    Convert README.md to RST via pandoc, and load into memory
    (fallback to LONG_DESCRIPTION on failure)
    """
    # Attempt to run pandoc on markdown file
    import subprocess
    try:
        subprocess.call(
            ['pandoc', '-t', 'rst', '-o', 'README.rst', 'README.md']
        )
    except OSError:
        return LONG_DESCRIPTION

    # Attempt to load output
    try:
        readme = open(os.path.join(
            os.path.dirname(__file__),
            'README.rst'
        ))
    except IOError:
        return LONG_DESCRIPTION
    return readme.read()


setup(
    name='wqxwq',
    version='0.0.1-dev',
    author='S. Andrew Sheppard',
    author_email='andrew@wq.io',
    license='MIT',
    description=LONG_DESCRIPTION.strip(),
    long_description=parse_markdown_readme(),
    packages=['wqxwq', 'wqxwq.migrations'],
    package_data={
        'wqxwq': [
            'mustache/*.*',
            'static/wqxwq/*.*',
        ]
    },
    install_requires=[
        'vera',
        'climata',
        'rest-pandas',
        'matplotlib',
        'data-wizard',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
        'Intended Audience :: Science/Research',
    ]
)
