# Copyright 2014 Luc Saffre
# License: BSD (see file COPYING for details)

from __future__ import unicode_literals

"""
Defines the :class:`DatePeriod` model mixin. and :class:`PeriodEvents`.
"""

import logging
logger = logging.getLogger(__name__)

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError

from lino.core.model import Model
from lino.utils.ranges import isrange


class DatePeriod(Model):

    """A model mixin for models which represent a period whose start and
end are date fields.

    """

    class Meta:
        abstract = True

    start_date = models.DateField(
        _("Start date"),
        blank=True, null=True)
    end_date = models.DateField(
        _("End date"),
        blank=True, null=True)

    def full_clean(self, *args, **kw):
        if not isrange(self.start_date, self.end_date):
            raise ValidationError(_("Date period ends before it started."))
        super(DatePeriod, self).full_clean(*args, **kw)


