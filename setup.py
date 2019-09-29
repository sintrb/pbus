from setuptools import setup
import os, io
from pbus import __version__

here = os.path.abspath(os.path.dirname(__file__))
README = io.open(os.path.join(here, 'README.md'), encoding='UTF-8').read()
CHANGES = io.open(os.path.join(here, 'CHANGES.md'), encoding='UTF-8').read()
setup(name="pbus",
      version=__version__,
      keywords=('pbus', 'bus', 'event', 'redis'),
      description="A simple application layer event-bus lib, support redis/mqtt/rabbitmq.",
      long_description=README + '\n\n\n' + CHANGES,
      long_description_content_type="text/markdown",
      url='https://github.com/sintrb/pbus/',
      author="trb",
      author_email="sintrb@gmail.com",
      packages=['pbus'],
      install_requires=[],
      zip_safe=False
      )
