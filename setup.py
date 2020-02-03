import os

from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='oauth2-client',
    version='0.1.2',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',
    description='OAuth2 Client for service to service communications',
    long_description=README,
    url='https://github.com/Livit/Labster.OAuth2Client',
    author='Labster',
    author_email='alexander@labster.com',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.8-2.2',  # replace "X.Y" as appropriate
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'django>=1.11.17,<=1.11.24;python_version=="2.7"',
        'django>=2.2;python_version>="3.7"',
        'psycopg2 >= 2.7.3',
        'pybreaker>=0.6.0',
        'requests_oauthlib>=1.2.0',
        'retrying>=1.3.3',
    ],
    extras_require={
        "oauth2provider_command": [
            'django-oauth-toolkit==1.0.0;python_version=="2.7"',
            'django-oauth-toolkit>=1.2.0;python_version>="3.7"',
        ],
        "JWT_grant": [
            'cryptography>=2.8',
        ],
    }
)
