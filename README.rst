SIMAGRI AGGREGATOR
==================

Simple configration of Vusion to play Aggregator for SIMAgri project. 

Dependencies
------------

#. `RabbitMQ <http://www.rabbitmq.com/>`_

Installation
------------

::

    $ virtualenv --no-site-packages ve
    $ source ve/bin/activate
    $ pip install -r requirements.pip

On initial setup RabbitMQ needs to be configured::

    $ sudo ./ve/src/vumi/utils/rabbitmq.setup.sh

Running
-------

::

	$ source ve/bin/activate
	$ supervisord


Tests
-----

::

	$ source ve/bin/activate
	$ trial tests
