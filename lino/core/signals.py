# Copyright 2013 Luc Saffre
# License: BSD (see file COPYING for details)

"""
This defines Lino's standard system signals.
"""

from django.dispatch import Signal, receiver

pre_analyze = Signal(['models_list'])
"""
Sent exactly once per process at site startup, 
just before Lino analyzes the models.

sender: 
  the Site instance
  
models_list:
  list of models 
  
"""

post_analyze = Signal(['models_list'])
"""
Sent exactly once per process at site startup, 
just after Site has finished to analyze the models.
"""


auto_create = Signal(["field", "value"])
"""
The :attr:`auto_create` signal is sent when 
:func:`lookup_or_create <>` silently created a model instance.

Arguments sent with this signal:

``sender``
    The model instance that has been created. 
    
``field``
    The database field 

``known_values``
    The specified known values

"""


pre_merge = Signal(['request'])
"""
Sent when a model instance is being merged into another instance.
"""

pre_remove_child = Signal(['request', 'child'])
pre_add_child = Signal(['request'])
pre_ui_create = Signal(['request'])
"""
Sent when a new model instance has been created and saved.
"""
pre_ui_update = Signal(['request'])

pre_ui_delete = Signal(['request'])
"""
Sent just before a model instance is being deleted using 
the user interface.

``request``:
  The HttpRequest object
  
"""

pre_ui_build = Signal()
post_ui_build = Signal()

database_connected = Signal()

#~ database_ready = Signal()


from django.db.models.fields import NOT_PROVIDED


class ChangeWatcher(object):

    """
    Utility to watch changes and send pre_ui_update
    """

    def __init__(self, watched):
        self.original_state = dict(watched.__dict__)
        self.watched = watched
        #~ self.is_new = is_new
        #~ self.request

    def is_dirty(self):
        #~ if self.is_new:
            #~ return True
        for k, v in self.original_state.iteritems():
            if v != self.watched.__dict__.get(k, NOT_PROVIDED):
                return True
        return False

    def send_update(self, request):
        #~ print "ChangeWatcher.send_update()", self.watched
        pre_ui_update.send(sender=self, request=request)
