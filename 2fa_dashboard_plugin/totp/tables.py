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

from django.template import defaultfilters
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import tables

from openstack_dashboard import settings
from openstack_dashboard.auth.backend import get_auth_url
from openstack_dashboard.auth.totp_oracle import TOTPOracle

LOG = logging.getLogger(__name__)
DEBUG = getattr(settings, 'TOTP_DEBUG', False)

# activate totp button link handler
class ActivateLink(tables.LinkAction):
    name = "activate"
    verbose_name = _("Activate TOTP Token")
    url = "horizon:identity:totp:activate"
    classes = ("ajax-modal",)
    icon = "plus"

    def allowed(self, request, datum):
        has_email_set = TOTPOracle(auth_url=get_auth_url(), user_data=request.user).user_get_email_address(request.user.id)

        if (self.table.data or (has_email_set == "None" or has_email_set is None)) and not DEBUG:
            return False
        return True

class RegenerateQRCode(tables.LinkAction):
    name = "regenerate"
    verbose_name = _("Display QRCode")
    url = "horizon:identity:totp:regenerate"
    classes = ("ajax-modal",)
    icon = "plus"

    def allowed(self, request, datum):
        has_email_set = TOTPOracle(auth_url=get_auth_url(), user_data=request.user).user_get_email_address(request.user.id)
        has_token_set = TOTPOracle(auth_url=get_auth_url(), user_data=request.user).user_get_totp_key(request.user.id)

        if ((has_email_set == "None" or has_email_set is None) or (has_token_set == "None" or has_token_set is None)) and not DEBUG:
            return False
        return True


# deactivate totp button link handler
class DeactivateLink(tables.DeleteAction):
    name = "deactivate"

    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Deactivate TOTP Token",
            u"Deactivate TOTP Token",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"TOTP Deactivated",
            u"TOTP Deactivated",
            count
        )

    def allowed(self, request, datum):
        return True

    def delete(self, request, obj_id):
        tokenmanager = TOTPOracle(auth_url=get_auth_url(), user_data=request.user)
        tokenmanager.disable(request.user.id)


class TwoFactorTable(tables.DataTable):
    STATUS_CHOICES = (
        ("true", True),
        ("false", False)
    )

    id = tables.Column('id', verbose_name=_('ID'), hidden=True)
    name = tables.Column('name', verbose_name=_('Openstack User ID'))
    seed = tables.Column('seed', verbose_name=_('Token Seed'))
    email = tables.Column('email', verbose_name=_('E-Mail Address'))
    enabled = tables.Column('enabled', verbose_name=_('Token Enabled'),
                            status=True,
                            status_choices=STATUS_CHOICES,
                            filters=(defaultfilters.yesno,
                                     defaultfilters.capfirst),
                            empty_value="False")

    class Meta(object):
        name = "totp"
        verbose_name = _("Two Factor Authentication")
        table_actions = (ActivateLink, DeactivateLink, RegenerateQRCode, )
