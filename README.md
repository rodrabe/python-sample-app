# python-sample-app

To run this as a developer:

 $ tox --notest
 $ .tox/py27/bin/gunicorn testapp

Then make a request like:

 $ curl http://127.0.0.1:8000

Here's a sample config file ( /etc/sample_app/sample_app.conf ):

 [sample_app]
 message = something
