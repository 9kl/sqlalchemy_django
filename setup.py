from setuptools import setup

setup(
    name='sqlalchemy_django',
    version='0.0.4',
    author='bigtiger',
    author_email='chinafengheping@gmail.com',
    url='http://www.hshl.ltd',
    description=u'similar flask sqlalchemy',
    packages=['sqlalchemy_django'],
    install_requires=[
        'SQLAlchemy>=1.1.11',
        'Django>=1.7.7'
    ]
)
