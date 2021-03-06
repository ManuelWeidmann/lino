# -*- coding: UTF-8 -*-
# Copyright 2011-2014 Luc Saffre
# License: BSD (see file COPYING for details)

"""Originally inspired by http://djangosnippets.org/snippets/650

Additions by LS:

- also logs a warning on the development server because that is easier
  to read than opening firebug and look at the response.

- must work also when :setting:`DEBUG` is False. Yes, on a production
  server it is not wise to publish the traceback, but our nice HTML
  formatted "Congratulations, you found a problem" page is never the
  right answer to an AJAX call.

"""

import sys
import traceback
from django.conf import settings
from django.http import HttpResponseServerError
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied


class AjaxExceptionResponse:

    def process_exception(self, request, exception):
        if request.is_ajax():
            (exc_type, exc_info, tb) = sys.exc_info()
            response = "%s\n" % exc_type.__name__
            response += "%s\n\n" % exc_info
            if settings.DEBUG:
                response += "TRACEBACK:\n"
                for tb in traceback.format_tb(tb):
                    #~ response += "%s\n" % tb
                    response += tb
                settings.SITE.logger.warning(
                    "AjaxExceptionResponse:\n" + response)
            else:
                settings.SITE.logger.exception(exception)
            if isinstance(exception, PermissionDenied):
                return HttpResponseForbidden(response)
            return HttpResponseServerError(response)
