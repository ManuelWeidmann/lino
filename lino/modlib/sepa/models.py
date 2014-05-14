# -*- coding: UTF-8 -*-
# Copyright 2014 Luc Saffre
# This file is part of the Lino project.
# Lino is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
# Lino is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public License
# along with Lino; if not, see <http://www.gnu.org/licenses/>.

"""
:xfile:`models.py` module for the :mod:`lino.modlib.sepa` app.

Defines the :class:`EventType` and :class:`Event` models and their tables.

There are some test cases in :mod:`lino.tutorials.mini.tests`

"""

from __future__ import unicode_literals

import logging
logger = logging.getLogger(__name__)

from django.db import models
from django.utils.translation import ugettext_lazy as _

from lino import dd

config = dd.apps.sepa

from ..iban.fields import IBANField, BICField
from ..iban.utils import belgian_nban_to_iban_bic, iban2bic


class IbanBicHolder(dd.Model):

    class Meta:
        abstract = True

    iban = IBANField(_("IBAN"))
    bic = BICField(_("BIC"), blank=True)

    def full_clean(self):
        super(IbanBicHolder, self).full_clean()
        if self.iban and not self.bic:
            if self.iban[0].isdigit():
                iban, bic = belgian_nban_to_iban_bic(self.iban)
                self.bic = bic
                self.iban = iban
            else:
                self.bic = iban2bic(self.iban) or ''


class Account(IbanBicHolder):
    """A bank account related to a given :class:`ml.contacts.Partner`.

    """
    class Meta:
        abstract = dd.is_abstract_model('sepa.Account')
        verbose_name = _("Account")
        verbose_name_plural = _("Accounts")

    partner = dd.ForeignKey(
        'contacts.Partner',
        related_name='sepa_accounts')
    remark = models.CharField(_("Remark"), max_length=200, blank=True)

    primary = models.BooleanField(
        _("Primary"),
        default=False,
        help_text=_(
            "Enabling this field will automatically disable any "
            "previous primary account and update "
            "the partner's IBAN and BIC"))

    allow_cascaded_delete = ['partner']

    def after_ui_save(self, ar):
        super(Account, self).after_ui_save(ar)
        if self.primary:
            mi = self.partner
            for o in mi.sepa_accounts.exclude(id=self.id):
                if o.primary:
                    o.primary = False
                    o.save()
                    ar.set_response(refresh_all=True)
            watcher = dd.ChangeWatcher(mi)
            for k in PRIMARY_FIELDS:
                setattr(mi, k, getattr(self, k))
            mi.save()
            watcher.send_update(ar.request)

PRIMARY_FIELDS = dd.fields_list(Account, 'iban bic')


class Accounts(dd.Table):
    model = 'sepa.Account'


class AccountsByPartner(Accounts):
    master_key = 'partner'
    column_names = 'iban bic remark'
    order_by = ['iban']
    auto_fit_column_widths = True


def setup_explorer_menu(site, ui, profile, m):
    m = m.add_menu(config.app_label, config.verbose_name)
    m.add_action('sepa.Accounts')
