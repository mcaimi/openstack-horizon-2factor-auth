# TOTP Verification Backend for Openstack Horizon
#
# Uses python-otp-lib https://github.com/mcaimi/python-otp-lib.git
#
# Changelog
#
# - Tue Jul 25 2017 - Initial porting to Horizon Mitaka - Marco Caimi <marco.caimi@fastweb.it>
# - Mon Nov 11 2019 - Porting to Openstack Stein. Move auth code from keystoneclient to keystoneauth1, drop support for keystone v2 - Marco Caimi <mcaimi@redhat.com>

import logging

# import python-otp-lib, TOTP
from rfc6238 import totp

# keystone client
from keystoneauth1.identity import v3 as v3_plugin
from keystoneclient.v3 import client as v3_client
from keystoneauth1 import session as keystone_session

# openstack dashboard api import
from openstack_dashboard.api import base as api_base
from openstack_dashboard.api import keystone

from openstack_dashboard import settings
from exception import IllegalArgument, InvalidToken, TOTPRuntimeError

LOG = logging.getLogger(__name__)
KS_VERSION = api_base.APIVersionManager('identity', preferred_version=3)

# custom keystone property to read from the database
TOTP_KEY_ATTRIBUTE = "totp_key"
EMAIL_ATTRIBUTE = "email"
KEYSTONE_URL = getattr(settings, "OPENSTACK_KEYSTONE_URL", None)
TOTP_TTL = getattr(settings, "TOTP_VALIDITY_PERIOD", 30)

# TOTP Token Oracle
# This class does all verification work.
class TOTPOracle(object):
    def __init__(self, auth_url=None, user_data=None, username=None, password=None, user_domain_name=None, project_domain_name=None, project_name=None):
        # sanity check. Either token or user/pass pair is needed to continue
        if not (user_data or (username and password)):
            raise IllegalArgument("[TOTPOracle.__init__()]: One either of token or username/password are required")

        self.__auth_url = auth_url
        if user_data:
            LOG.info("[TOTP]: using keystone v3.")
            if KEYSTONE_URL:
                self.auth = v3_plugin.Token(auth_url=settings.OPENSTACK_KEYSTONE_URL, 
                                        project_id=user_data.project_id, 
                                        project_domain_id=user_data.domain_id, 
                                        token=user_data.token.id)
            else:
                raise TOTPRuntimeError("[TOTPOracle.__init__()]: Missing OPENSTACK_KEYSTONE_URL or OPENSTACK_HOST in Horizon local_settings")

            # create a session
            self.ks_session = keystone_session.Session(auth=self.auth)
        else:
            LOG.info("[TOTP] using keystone v3 with username/password pair")
            self.auth = v3_plugin.Password(auth_url=auth_url, username=username, password=password, 
                                            project_name = project_name,
                                            project_domain_name = project_domain_name,
                                            user_domain_name=user_domain_name)
            
            # build session
            self.ks_session = keystone_session.Session(auth=self.auth)

    # get keystone client
    def __get_client(self):
        return v3_client.Client(session=self.ks_session)

    # query keystone for user info
    def user_get(self, user_id):
        client = self.__get_client()
        return client.users.get(user_id)

    # get totp auth key from user's extra specs
    def user_get_totp_key(self, user_id):
        user = self.user_get(user_id)
        seed = getattr(user, TOTP_KEY_ATTRIBUTE, None)

        if seed == "":
            seed = None

        if isinstance(seed, str):
            return seed
        else:
            return str(seed)

    # get user's e-mail address from the keystone database
    def user_get_email_address(self, user_id):
        user = self.user_get(user_id)

        email = getattr(user, EMAIL_ATTRIBUTE, None)

        if isinstance(email, str):
            return email
        else:
            return str(email)

    # verify totp token
    def validate(self, user_id, otp=None):
        # get totp key
        key = self.user_get_totp_key(user_id)

        # user does not have totp enabled.
        if ((key == "None") or (key is None)) and not otp:
            return True

        # handle invalid token
        if not key:
            raise InvalidToken("[TOTPOracle.validate()] - Invalid token")

        # calculate totp token
        totp_token = totp.TOTP(key, timestep=TOTP_TTL)

        # check and return
        return (str(otp) == str(totp_token))

    # enable totp by saveing the totp key in keystone
    def enable(self, user_id, key, otp):
        t = totp.TOTP(key)
        if not (str(t) == str(otp)):
            raise InvalidToken("[TOTPOracle.enable()] - Token error")

        client = self.__get_client()
        client.users.update(user_id, totp_key=key)

    # disable totp by clearing out the extra spec that contains the totp key
    def disable(self, user_id):
        client = self.__get_client()
        client.users.update(user_id, totp_key="")

