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

import logging

from rfc6238 import totp

from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import settings
from openstack_dashboard.auth.backend import get_auth_url
from openstack_dashboard.auth.totp_oracle import TOTPOracle
from openstack_dashboard.dashboards.identity.totp.activation_email import send_activation_email

LOG = logging.getLogger(__name__)

# TOTP Django form
class ActivateTwoFactorForm(forms.SelfHandlingForm):
    token = forms.CharField(max_length=255, label=_("Token"))
    seed = forms.CharField(label=_("Seed"),
                           required=False,
                           widget=forms.HiddenInput())
    email_address = forms.CharField(label=_("E-Mail"),
                           required=False,
                           widget=forms.HiddenInput())


    def __init__(self, request, *args, **kwargs):
        super(ActivateTwoFactorForm, self).__init__(request, *args, **kwargs)
        v_seed = kwargs.get('data', {}).get('seed')
        email = TOTPOracle(auth_url=get_auth_url(), user_data=request.user).user_get_email_address(request.user.id)

        if not v_seed:
            v_seed = totp.get_random_base32_key(byte_key=16)
            kwargs.get('initial', {})['seed'] = v_seed
            if (email == "") or (email == "None") or (email is None):
                email = "MissingField"
            else:
                # send email...
                 send_activation_email(sender=getattr(settings, 'ACTIVATION_EMAIL_ADDRESS', 'activation@provider.tld'), 
                                        recipient=email, 
                                        subject=getattr(settings, 'ACTIVATION_EMAIL_SUBJECT', 'TOTP Activation'), 
                                        totp_token=v_seed, 
                                        request=request)

        self.fields['seed'].initial = v_seed
        self.fields['email_address'].initial = email

    def handle(self, request, data):
        user = self.request.user
        try:
            token_seed = data.get("seed")
            token_otp = data.get("token")
            #user_email = data.get("email_address")
            twofactor = TOTPOracle(auth_url=get_auth_url(), user_data=user)
            twofactor.enable(user.id, token_seed, token_otp)
            messages.success(request, _('[2FA]: Two Factor Auth successfully enabled.'))
        except:
            exceptions.handle(request, _('[2FA]: Error while enabling two factor authentication plugin.'))

        return True 

class RegenerateTwoFactorForm(forms.SelfHandlingForm):
    seed = forms.CharField(label=_("Seed"),
                           required=False,
                           widget=forms.HiddenInput())
    email_address = forms.CharField(label=_("E-Mail"),
                           required=False,
                           widget=forms.HiddenInput())


    def __init__(self, request, *args, **kwargs):
        super(RegenerateTwoFactorForm, self).__init__(request, *args, **kwargs)
        v_seed = TOTPOracle(auth_url=get_auth_url(), user_data=request.user).user_get_totp_key(request.user.id)
        if not v_seed:
            return False

        email = TOTPOracle(auth_url=get_auth_url(), user_data=request.user).user_get_email_address(request.user.id)
        if (email == "None") or (email is None):
            email = "MissingField"

        self.fields['seed'].initial = v_seed
        self.fields['email_address'].initial = email

    def handle(self, request, data):
        return True
