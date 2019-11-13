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

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from horizon import exceptions
from horizon import forms
from horizon import tables

from openstack_dashboard import settings
from openstack_dashboard.auth.backend import get_auth_url
from openstack_dashboard.auth.totp_oracle import TOTPOracle
from openstack_dashboard.dashboards.identity.totp import forms as totp_forms
from openstack_dashboard.dashboards.identity.totp import tables as totp_tables
from openstack_dashboard.dashboards.identity.totp.tools import qr as QR

LOG = logging.getLogger(__name__)


class TwoFactorData(object):
    def __init__(self, id, name, seed, enabled, email):
        self.id = id
        self.name = name
        self.seed = seed
        self.email = email
        self.enabled = enabled


class IndexView(tables.DataTableView):
    table_class = totp_tables.TwoFactorTable
    template_name = 'identity/totp/index.html'
    page_title = _("Two Factor Authentication")
    
    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data(**kwargs)
        manager = TOTPOracle(auth_url=get_auth_url(), user_data=self.request.user)
        email_address = manager.user_get_email_address(self.request.user.id)
        if email_address == "None" or email_address is None:
                context['emailaddress'] = "MissingField"
        else:
                context['emailaddress'] = email_address

        return context

    def get_data(self):
        objects = []
        try:
            manager = TOTPOracle(auth_url=get_auth_url(), user_data=self.request.user)
            totp_key = manager.user_get_totp_key(self.request.user.id)
            email = manager.user_get_email_address(self.request.user.id)
            if (email == "None") or (email is None):
                email = "MissingAddress"

            if totp_key and not ((totp_key == "None") or (totp_key is None)):
                objects.append(TwoFactorData(self.request.user.id, self.request.user.username, totp_key, True, email))
        except:
            objects = [] 

        return objects


class ActivateView(forms.ModalFormView):
    template_name = 'identity/totp/activate.html'
    modal_header = _("Activate TOTP Authentication")
    form_id = "activate_totp_form"
    form_class = totp_forms.ActivateTwoFactorForm
    submit_label = _("Activate Token")
    submit_url = reverse_lazy("horizon:identity:totp:activate")
    success_url = reverse_lazy('horizon:identity:totp:index')
    page_title = _("Activate TOTP Authentication")

class RegenerateView(forms.ModalFormView):
    template_name = 'identity/totp/regenerate.html'
    modal_header = _("Add a TOTP SoftToken")
    form_id = "regenerate_totp_form"
    form_class = totp_forms.RegenerateTwoFactorForm
    submit_label = _("Close")
    action_url = None
    submit_url = reverse_lazy("horizon:identity:totp:regenerate")
    success_url = reverse_lazy('horizon:identity:totp:index')

# generate qrcode
def qr(request, token_seed=None, html_encode=True):
    return QR(request=request, token_seed=token_seed, html_encode=html_encode)

