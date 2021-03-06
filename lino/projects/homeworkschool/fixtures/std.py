# -*- coding: UTF-8 -*-
# Copyright 2012 Luc Saffre
# License: BSD (see file COPYING for details)


from lino.utils.instantiator import Instantiator, i2d
from lino.core.dbutils import resolve_model
from django.utils.translation import ugettext_lazy as _


from django.conf import settings
from north.dbutils import babel_values


def objects():

    mailType = Instantiator('notes.NoteType').build

    yield mailType(**babel_values('name',
                                  en="Enrolment",
                                  fr=u'Inscription', de=u"Einschreibeformular"))
    yield mailType(**babel_values('name',
                                  en="Timetable",
                                  fr=u'Horaire', de=u"Stundenplan"))
    yield mailType(**babel_values('name',
                                  en="Letter",
                                  fr=u'Lettre', de=u"Brief"))
