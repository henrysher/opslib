.. _getting-started:

===========================
Getting Started with OpsLib
===========================

This tutorial will walk you through installing and configuring ``OpsLib``, as
well how to use it to make API calls.

This tutorial assumes you are familiar with Python & that you have registered
for an `Amazon Web Services`_ account. You'll need retrieve your
``Access Key ID`` and ``Secret Access Key`` from the web-based console.

.. _`Amazon Web Services`: https://aws.amazon.com/


Installing OpsLib
-----------------

You can use ``pip`` to install the latest released version of ``OpsLib``::

    pip install opslib


Configuring OpsLib Credentials
---------------------------------

You have a few options for configuring ``OpsLib``
For this tutorial, we'll be using a configuration file. 

Default Configuration
=====================
There is a ``...site-packages/opslib/opslib.ini`` file with these contents::

    [Credentials]
    aws_access_key_id = 
    aws_secret_access_key = 
     
    [Boto]
    num_retries = 5
    http_socket_timeout = 70
    metadata_service_num_attempts = 5
    metadata_service_timeout = 70

Please fill in ``Credentials`` section with your AWS credentials.
If you would like to use ``IAM Role``, just let it be **empty** here.

Customized Configuration
========================
For your own customized configuration, 
follow the format with the default configuration above 
show the path to ``opslib`` module when you try to import it::
   
    import opslib
    opslib.init_config("/path/your_own_config_file")


Logging Configuration
---------------------
By default, when you import ``opslib`` module, it will not enable console output
or write logs to log file. So you have to enable it by yourself::

    import opslib
    opslib.init_logging(name="log_handler", logfile="/path/your_log_file", 
                        console=True, loglevel="info")


Next Steps
----------

For many of the services that ``OpsLib`` supports, there are tutorials as
well as detailed API documentation. 
If you are interested in a specific service, the tutorial for the service 
is a good starting point. 
For instance, if you'd like more information on IcsEc2, check out the 
:doc:`IcsEc2 API reference <icsec2>`.

Here comes an example -  we need to fetch all the tags of instance "i-123456" in "us-east-1" region::

    import opslib
    from opslib.icsec2 import IcsEc2
    ec2 = IcsEc2("us-east-1")
    tags = ec2.get_instance_tags("i-12345678")




