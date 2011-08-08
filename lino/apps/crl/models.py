## Copyright 2011 Luc Saffre
## This file is part of the Lino project.
## Lino is free software; you can redistribute it and/or modify 
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 3 of the License, or
## (at your option) any later version.
## Lino is distributed in the hope that it will be useful, 
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
## GNU General Public License for more details.
## You should have received a copy of the GNU General Public License
## along with Lino; if not, see <http://www.gnu.org/licenses/>.
"""
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _


from lino import reports
from lino import mixins
from lino.models import SiteConfig
from lino.modlib.countries import models as countries
from lino.modlib.contacts import models as contacts
from lino.modlib.notes import models as notes
from lino.modlib.links import models as links
from lino.modlib.cal import models as cal

class Person(contacts.Born,contacts.Person):
    class Meta(contacts.Person.Meta):
        app_label = 'contacts'
        # see :doc:`/tickets/14`
        #~ verbose_name = _("Person")
        #~ verbose_name_plural = _("Persons")
    died_date = models.DateField(
        blank=True,null=True,
        verbose_name=_("Died date"))

              
class Company(contacts.Company):
    class Meta(contacts.Company.Meta):
        app_label = 'contacts'
        # see :doc:`/tickets/14`
        #~ verbose_name = _("Company")
        #~ verbose_name_plural = _("Companies")
    
class Note(notes.Note,mixins.Owned):
     class Meta(notes.Note.Meta):
        app_label = 'notes'
        # see :doc:`/tickets/14`
        #~ verbose_name = _("Note")
        #~ verbose_name_plural = _("Notes")
 
class Event(cal.Event):
    class Meta(cal.Event.Meta):
        app_label = 'cal'

class Task(cal.Task):
    class Meta(cal.Task.Meta):
        app_label = 'cal'

        
        



#
# LINKS
#
class Link(links.Link,mixins.Owned):
    class Meta:
        app_label = 'links'

class LinksByOwner(links.LinksByOwnerBase):
    fk_name = 'owner'
    column_names = "name url user date *"
    order_by = ["date"]
  
from lino.utils import crl2hex, hex2crl, CRL

class CrlField(models.CharField):
    __metaclass__ = models.SubfieldBase # needed for to_python() to be called automatically.
    def __init__(self, *args, **kw):
        defaults = dict(
            verbose_name=_("Label"),
            max_length=100,
            blank=True, 
            )
        defaults.update(kw)
        models.CharField.__init__(self,*args, **defaults)
        
    def to_python(self, value):
        if not value: return value
        if isinstance(value,CRL):
            return value
        return CRL(hex2crl(value))

    def get_prep_value(self, value):
        if not value: return value
        assert isinstance(value,CRL)
        return crl2hex(value)
        

reports.inject_field(countries.City,'crl',CrlField())
reports.inject_field(Person,'crl',CrlField())
reports.inject_field(Company,'crl',CrlField())

