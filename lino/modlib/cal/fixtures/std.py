# -*- coding: UTF-8 -*-
# Copyright 2011-2014 Luc Saffre
# License: BSD (see file COPYING for details)

"""
Installs standard values for :mod:`lino.modlib.cal`,
including a demo set of holidays.
(TODO: make them more configurable.)

"""

from __future__ import unicode_literals

import datetime
from dateutil.relativedelta import relativedelta
ONE_DAY = relativedelta(days=1)

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext as _


from lino.utils import i2d
from lino.utils.instantiator import Instantiator
from lino.core.dbutils import resolve_model
from north.dbutils import babel_values

from lino import dd, rt

cal = dd.resolve_app('cal')


def objects():

    #~ add = Instantiator('cal.EventStatus','ref').build
    #~ yield add('0',**babel_values('name',en=u"tentative",de=u"Vorschlag",   fr=u"proposition"))
    #~ yield add('1',**babel_values('name',en=u"confirmed",de=u"bestätigt",   fr=u"confirmé"))
    #~ yield add('2',**babel_values('name',en=u"cancelled",de=u"storniert",   fr=u"annulé"))
    #~ yield add('3',**babel_values('name',en=u"rescheduled",de=u"verschoben",   fr=u"reporté"))
    #~ yield add('4',**babel_values('name',en=u"absent",de=u"abwesend",   fr=u"absent"))

    #~ add = Instantiator('cal.TaskStatus','ref').build
    #~ yield add('0',**babel_values('name',en=u"needs action",de=u"zu erledigen",   fr=u"à traîter"))
    #~ yield add('1',**babel_values('name',en=u"in process",de=u"begonnen",   fr=u"commencée"))
    #~ yield add('2',**babel_values('name',en=u"completed",de=u"erledigt",   fr=u"complétée"))
    #~ yield add('3',**babel_values('name',en=u"cancelled",de=u"storniert",   fr=u"annulée"))
    #~ add = Instantiator('cal.AccessClass','ref').build
    #~ yield add('0',**babel_values('name',en=u"Public",de=u"Öffentlich",   fr=u"Public"))
    #~ yield add('1',**babel_values('name',en=u"Private",de=u"Privat",   fr=u"Privé"))
    #~ yield add('2',**babel_values('name',en=u"Confidential",de=u"Vertraulich",   fr=u"Confidentiel"))
    add = Instantiator('cal.Priority', 'ref').build
    yield add('1', **babel_values('name', en=u"very urgent", de=u"sehr dringend",   fr=u"très urgent", et=u"väga kiire"))
    # yield add('2', **babel_values('name', en=u"quite urgent", de=u"recht dringend",   fr=u"relativement urgent"))
    yield add('3', **babel_values('name', en=u"urgent", de=u"dringend",   fr=u"urgent", et="kiire"))
    # yield add('4', **babel_values('name', en=u"relatively urgent", de=u"ziemlich dringend",   fr=u"relativement urgent"))
    yield add('5', **babel_values('name', en=u"normal", de=u"normal",   fr=u"normal", et="keskmine"))
    # yield add('6', **babel_values('name', en=u"not very urgent", de=u"nicht sehr niedrig",   fr=u"pas très urgent"))
    # yield add('7', **babel_values('name', en=u"not urgent", de=u"nicht dringend",   fr=u"pas urgent"))
    yield add('9', **babel_values('name', en=u"not urgent", de=u"nicht dringend",   fr=u"pas urgent", et="mitte kiire"))
    # yield add('9', **babel_values('name', en=u"not urgent at all", de=u"überhaupt nicht dringend",   fr=u"pas urgent du tout"))

    calendar = Instantiator('cal.Calendar').build
    general = calendar(**dd.str2kw('name', _("General")))
                                    # de="Allgemein",
                                    # fr="Général",
    yield general
    settings.SITE.site_config.site_calendar = general
    #~ settings.SITE.site_config.holiday_event_type = holidays
    yield settings.SITE.site_config

    event_type = Instantiator('cal.EventType').build
    holidays = event_type(all_rooms=True,
                          **dd.str2kw('name', _("Holidays")))
                                   #     de="Feiertage",
                                   #     fr="Jours fériés",
    yield holidays

    RecurrentEvent = dd.resolve_model('cal.RecurrentEvent')
    add = Instantiator(RecurrentEvent, event_type=holidays).build

    def holiday(month, day, en, de, fr, et=None):
        if et is None:
            et = en
        return add(
            every_unit=cal.Recurrencies.yearly,
            monday=True, tuesday=True, wednesday=True, thursday=True,
            friday=True, saturday=True, sunday=True,
            every=1,
            start_date=datetime.date(
                year=cal.DEMO_START_YEAR,
                month=month, day=day),
            **dd.babelkw('name', en=en, de=de, fr=fr, et=et))
    yield holiday(1, 1, "New Year's Day", "Neujahr", "Jour de l'an", "Uusaasta")
    yield holiday(5, 1, "International Workers' Day", "Tag der Arbeit", "Premier Mai", "kevadpüha")
    yield holiday(7, 21, "National Day", "Nationalfeiertag", "Fête nationale", "Belgia riigipüha")
    yield holiday(8, 15, "Assumption of Mary", "Mariä Himmelfahrt", "Assomption de Marie")
    yield holiday(10, 31, "All Souls' Day", "Allerseelen", "Commémoration des fidèles défunts")
    yield holiday(11, 1, "All Saints' Day", "Allerheiligen", "Toussaint")
    yield holiday(11, 11, "Armistice with Germany", "Waffenstillstand", "Armistice")
    yield holiday(12, 25, "Christmas", "Weihnachten", "Noël", "Esimene Jõulupüha")

    summer = holiday(07, 01, "Summer holidays", "Sommerferien", "Vacances d'été", "Suvevaheaeg")
    summer.end_date = summer.start_date.replace(month=8, day=31)
    yield summer

    ar = settings.SITE.login()
    for obj in RecurrentEvent.objects.all():
        if not obj.update_reminders(ar):
            raise Exception("Oops, %s generated no events" % obj)
