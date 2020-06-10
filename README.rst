===========================================
Openstack Horizon Two Factor Authentication
===========================================

This plugin adds a second factor to the Horizon Authentication facility using the 
TOTP protocol.

This plugin was written for our Openstack Cloud back in 2015 (on Openstack Juno) and then 
more or less abandoned.

The codebase was cleaned up and reworked in 2017 as we updated our Openstack installation 
to the Mitaka Release and Newton afterwards.

The master branch is developed on top of RDO latest release (currently this is "Ussuri").
The latest environment makes use of:

- RHEL/CentOS 8.x Branch
- Python 3.6+

This version does not depend on external totp libraries and is implemented in pure python: 
it was developed on RedHat's own Openstack distribution but it shoud work on any openstack
horizon dashboard flavor.

The plugin is composed of these modules:

- The Authentication Backend (2fa_auth_plugin folder)
- The Horizon Dashboard (2fa_dashboard_plugin folder)

A management script and library RPM spec is also provided.

How to install and configure
============================

These are the basic installation steps for Openstack Horizon:

First you have to build an RPM package from the totp-lib submodule in the git project.

On CentOS 8, set the default interpreter to the local python3 version:

.. code:: bash

  # alternatives --set python /usr/bin/python3

And then build the otp-lib package:

.. code:: bash

  # dnf install -y rpm-build git python-setuptools-wheel python3-setuptools-wheel
  # mkdir -p ~/rpmbuild/{SRPMS,RPMS,SOURCES,SPECS} && cd ~/rpmbuild
  # git clone https://github.com/mcaimi/python-otp-lib.git python-otp-lib-ussuri
  # tar cjvf SOURCES/python-otp-lib-ussuri-1.tar.gz python-otp-lib-ussuri

Now, copy the SPEC file from this repo in `~/rpmbuild/SPECS` and build the RPM package:

.. code:: bash

  # rpmbuild -bb SPECS/python-otp-lib-ussuri.spec

Install prerequisites (totp-lib, python-qrcode)
-----------------------------------------------

If you are on a RedHat/CentOS distro, first install the python-qrcode RPM package, then 
install the RPM package just built before:

.. code:: bash

  # dnf install -y python3-qrcode python3-qrcode-core
  # rpm -ivH python-otp-lib-ussuri-1.x86_64.rpm 

Install the TOTP Authentication Backend and Dashboard
-----------------------------------------------------

On every Horizon node you happen to have deployed in your environment, install the new django
dashboard. It will show up under the 'Identity' tab:

.. code:: bash 

  # cp -rv 2fa_dashboard_plugin/totp /usr/share/openstack-dashboard/openstack_dashboard/dashboards/identity/

Next the actual auth backend must be put in place:

.. code:: bash 
  
  # mkdir -p /usr/share/openstack-dashboard/openstack_dashboard/auth
  # cp -v 2fa_auth_plugin/* /usr/share/openstack-dashboard/openstack_dashboard/auth/

Configure Django Settings
-------------------------

On all horizon nodes, edit `/usr/share/openstack-dashboard/openstack_dashboard/settings.py` and
set this parameters to change the authentication python class used by django:

.. code:: python

  TOTP_DEBUG = False
  TOTP_VALIDITY_PERIOD = 30
  AUTHENTICATION_BACKENDS = ('openstack_auth.backend.KeystoneBackend',)


with

.. code:: python

  AUTHENTICATION_BACKENDS =('openstack_dashboard.auth.backend.TwoFactorAuthBackend',)

and in /etc/openstack-dashboard/local_settings:

.. code:: python

  # Send email to the console by default
  EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
  # Configure these for your outgoing email host
  EMAIL_HOST = '<your mail server>'
  EMAIL_PORT = <your mail server port>
  # Activation email
  ACTIVATION_EMAIL_ADDRESS = "noreply@cloud-provider.tld"
  ACTIVATION_EMAIL_SUBJECT = "TOTP Activation Message"

Openstack Queens and Later:
---------------------------

Set up keystone policies directory if not already done:

.. code:: bash

  # under /etc/keystone/keystone.conf
  policies_dir = /etc/keystone/policy.d

  # create directory
  $ mkdir -p /etc/keystone/policy.d

Fix Keystone policies to allow the token owner to update the user on keystone:

.. code:: bash

  # in /etc/openstack-dashboard/keystone_policy.json update the 'identity:update_user' policy to match this:

  "identity:update_user": "rule:admin_required or rule:admin_and_matching_target_user_domain_id or rule:owner",

  # create a file under /etc/keystone/policy.d called update_user.json and insert these lines inside:

  {
    "identity:update_user": "rule:admin_required or rule:admin_and_matching_target_user_domain_id or rule:owner"
  }

the previous line uses policy.v3cloudsample.json as a base template (see the official keystone GitHub repo for that).

Enable the newly installed dashboard
------------------------------------

Lastly, enable the dashboard:

.. code:: bash

  # cp -v 2fa_dashboard_plugin/enabled/_3032_identity_totp_panel.py /usr/share/openstack-dashboard/openstack_dashboard/dashboards/enabled/
  # restorecon -Rv /usr/share/openstack-dashboard
  # systemctl restart httpd

