#!/usr/bin/env python
from setuptools import setup


setup(
    name='django-whisper',
    version='0.2.3',
    description='Chat with rooms for Django based on websockets',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Pragmatic Mates',
    author_email='info@pragmaticmates.com',
    maintainer='Pragmatic Mates',
    maintainer_email='info@pragmaticmates.com',
    url='https://github.com/PragmaticMates/django-whisper',
    packages=[
        'whisper',
        'whisper.migrations',
        'whisper.templatetags'
    ],
    include_package_data=True,
    install_requires=('django', 'channels'),
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Framework :: Django',
        'License :: OSI Approved :: BSD License',
        'Development Status :: 3 - Alpha'
    ],
    license='BSD License',
    keywords="django chat room channels websocket",
)
