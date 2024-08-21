import sys

from setuptools import setup

install_requires = [
    'awscli >= 1.33',
    'boto3 >= 1.34',
    'yattag >= 1.16',
    'wheel >= 0.37.1',
    'pip >= 22.0.2',
    'six >= 1.16.0',
]

setup(
    name='mkwheelhouse',
    version='1.1.1',
    author='Nikhil Benesch',
    author_email='benesch@whoop.com',
    py_modules=['mkwheelhouse'],
    url='https://github.com/WhoopInc/mkwheelhouse',
    description='Amazon S3 wheelhouse generator',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools'
    ],
    install_requires=install_requires,
    extras_require={
        'tests': [
            'pre-commit'
        ]
    },
    entry_points={
        'console_scripts': [
            'mkwheelhouse=mkwheelhouse:main'
        ],
    }
)
