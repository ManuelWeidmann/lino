from lino.apps.std.settings import *
class Lino(Lino):
    user_model = None
    use_contenttypes = False
    
    abstract_address = True
    """
    If True, then the Addresses model is abstract 
    (i.e. we don't have a separate table for Addresses).
    After changing this setting, you must rebuild the database.
    """

    def get_app_source_file(self):
        return __file__
        
    def setup_quicklinks(self,ui,user,tb):
        tb.add_action(self.modules.contacts.Persons.detail_action)
        tb.add_action(self.modules.contacts.Companies.detail_action)
        
        
    def setup_menu(self,ui,user,main):
        from django.utils.translation import ugettext_lazy as _
        from django.db import models
        
        m = main.add_menu("master",_("Master"))
        self.modules.contacts.setup_main_menu(self,ui,user,m)

        m = main.add_menu("config",_("Configure"))
        self.modules.contacts.setup_config_menu(self,ui,user,m)

        m = main.add_menu("explorer",_("Explorer"))
        self.modules.contacts.setup_explorer_menu(self,ui,user,m)
        
        m = main.add_menu("site",_("Site"))
        self.modules.lino.setup_site_menu(self,ui,user,m)

LINO = Lino(__file__,globals())    

INSTALLED_APPS = (
  #~ 'django.contrib.contenttypes', 
  'lino.modlib.countries', 
  'lino', 
  'lino.sandbox.contacts', 
)

DEBUG = True

DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.sqlite3',
          'NAME': join(LINO.project_dir,'test.db')
          #~ 'NAME': ':memory:'
      }
  }