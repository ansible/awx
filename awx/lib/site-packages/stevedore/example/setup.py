from setuptools import setup, find_packages

setup(
    name='stevedore-examples',
    version='1.0',

    description='Demonstration package for stevedore',

    author='Doug Hellmann',
    author_email='doug.hellmann@dreamhost.com',

    url='https://github.com/dreamhost/stevedore',
    download_url='https://github.com/dreamhost/stevedore/tarball/master',

    classifiers=['Development Status :: 3 - Alpha',
                 'License :: OSI Approved :: Apache Software License',
                 'Programming Language :: Python',
                 'Programming Language :: Python :: 2',
                 'Programming Language :: Python :: 2.7',
                 'Programming Language :: Python :: 3',
                 'Programming Language :: Python :: 3.2',
                 'Programming Language :: Python :: 3.3',
                 'Intended Audience :: Developers',
                 'Environment :: Console',
                 ],

    platforms=['Any'],

    scripts=[],

    provides=['stevedore.examples',
              ],

    packages=find_packages(),
    include_package_data=True,

    entry_points={
        'stevedore.example.formatter': [
            'simple = stevedore.example.simple:Simple',
            'field = stevedore.example.fields:FieldList',
            'plain = stevedore.example.simple:Simple',
        ],
    },

    zip_safe=False,
)
