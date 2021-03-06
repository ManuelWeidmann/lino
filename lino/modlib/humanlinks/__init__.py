# Copyright 2014 Luc Saffre
# License: BSD (see file COPYING for details)

"See :mod:`ml.humanlinks`."

from lino import ad

from django.utils.translation import ugettext_lazy as _


class Plugin(ad.Plugin):
    "Ceci n'est pas une documentation."
    verbose_name = _("Parency links")

    ## settings
    person_model = 'contacts.Person'

