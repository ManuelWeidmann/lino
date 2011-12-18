# -*- coding: UTF-8 -*-
## Copyright 2010-2011 Luc Saffre
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

Lino's authentification utilities


"""

import os
import logging
logger = logging.getLogger(__name__)


from django.utils import translation
from django.conf import settings

from lino.tools import resolve_model
from lino.utils import babel

class NoUserMiddleware(object):
    """
    Middleware that will be used on sites with 
    empty :attr:`lino.Lino.user_model`.
    It just adds a `user` attribute whose value is None.
    """
    def process_request(self, request):
        request.user = None
        
        

if settings.LINO.user_model:
  
    USER_MODEL = resolve_model(settings.LINO.user_model)

    class RemoteUserMiddleware(object):
        """
        This does the same as
        `django.contrib.auth.middleware.RemoteUserMiddleware`, 
        but in a simplified manner and without using Sessions.
        
        It also activates the User's language, if that field is not empty.
        Since it will run *after*
        `django.contrib.auth.middleware.RemoteUserMiddleware`
        (at least if you didn't change :meth:`lino.Lino.get_middleware_classes`),
        it will override any browser setting.
        
        """

        def process_request(self, request):
          
            username = request.META.get(settings.LINO.remote_user_header,settings.LINO.default_user)
            if not username:
                raise Exception("No %s in %s" % (settings.LINO.remote_user_header,request.META))
                
            try:
                request.user = USER_MODEL.objects.get(username=username)
            except USER_MODEL.DoesNotExist,e:
                u = USER_MODEL(username=username)
                u.full_clean()
                u.save()
                logger.info("Creating new user %s from request %s",u,request)
                request.user = u
            
            if len(babel.AVAILABLE_LANGUAGES) > 1:
                if request.user.language:
                    translation.activate(request.user.language)
                    request.LANGUAGE_CODE = translation.get_language()
            
        