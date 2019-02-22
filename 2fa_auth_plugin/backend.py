# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Changelog
#
# - Tue Jul 25 - Initial porting to Horizon Mitaka - Marco Caimi <marco.caimi@fastweb.it>

""" Module defining the Django auth backend class for the Two Factor API. """

import logging
import urlparse

from openstack_auth import backend
from openstack_auth import exceptions

from totp_oracle import TOTPOracle
from openstack_dashboard import settings

LOG = logging.getLogger(__name__)

KEYSTONE_CLIENT_ATTR = "_keystoneclient"

# get authentication url from django's own configuration
def get_auth_url():
    auth_url = getattr(settings, 'OPENSTACK_KEYSTONE_URL')
    auth_url = auth_url.rstrip('/')
    return urlparse.urljoin(auth_url, 'v3')

# authentication backend custom provider class
# this overrides the default in settings.py
class TwoFactorAuthBackend(backend.KeystoneBackend):
    def authenticate(self, request=None, username=None, password=None, user_domain_name=None, project_domain_name=None, auth_url=None):
        # try authentication with otp....
        try:
            # last six digits is the OTP token
            otp = password[-6::]
            # authenticate with user/pass, with pass being the password from the login page
            # minus the last six characters
            user = super(TwoFactorAuthBackend, self).authenticate(request=request,
                                                               username=username,
                                                               password=password[:-6:],
                                                               user_domain_name=user_domain_name,
                                                               project_domain_name=project_domain_name,
                                                               auth_url=auth_url)
            LOG.info('[OTP Preauth Phase - Keystone] - User [%s] authenticated on keystone (with correct-sized otp token)' % username)
        # or fallback to normal keystone username/pass combo
        except:
            # no otp now...
            otp = None

            # authenticate on keystone
            user = super(TwoFactorAuthBackend, self).authenticate(request=request,
                                                               username=username,
                                                               password=password,
                                                               user_domain_name=user_domain_name,
                                                               project_domain_name=project_domain_name,
                                                               auth_url=auth_url)
            LOG.info('[OTP Preauth Phase - Keystone] - User [%s] authenticated on keystone (without otp token or no otp)' % username)

        # verify the authentication token if applicable
        try:
            oracle = TOTPOracle(auth_url=get_auth_url(), user_data=user)
            if not oracle.validate(user.id, otp=otp):
                LOG.info("[OTP Postauth Phase - TOTP] - Token invalid or expired for user [%s] " % username)
                raise exceptions.KeystoneAuthException("[OTP Keystone Backend] - Invalid otp token, user not authenticated.")

            LOG.info("[OTP Postauth Phase - TOTP] - Token for user [%s] is valid: Authentication Complete" % username)
            return user
        except Exception as e:
            raise exceptions.KeystoneAuthException(e.message)
