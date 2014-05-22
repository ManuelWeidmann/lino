===========
Runtime API
===========

This section documents classes which are important at runtime.

.. currentmodule:: rt


The ``ActionRequest`` class
---------------------------

.. class:: ActionRequest

    An action request is when a given user asks to run a given action
    of a given actor.

    Every Django web request is wrapped into an action request.

    But an ActionRequest also holds extended information about the
    "context" (like the "renderer" being used) and provides the
    application with methods to communicate with the user.

    A bare BaseRequest instance is returned as a "session" by
    :meth:`login <lino.site.Site.login>`.



  .. method:: show(self, spec, master_instance=None,
                   column_names=None, header_level=None, 
                   language=None, **kw)

    Show the specified table or action using the current renderer.  If
    the table is a :term:`slave table`, then a `master_instance` must
    be specified as second argument.

    The first argument, `spec` can be:
    - a string with the name of a model, actor or action
    - another action request
    - a bound action (i.e. a :class:`BoundAction` instance)

    Optional keyword arguments are

    - `column_names` overrides default list of columns
    - `header_level` show also the header (using specified level)
    - `language` overrides the default language used for headers and
      translatable data

    Any other keyword arguments are forwarded to :meth:`spawn`.

    Usage in a tested doc::

      >>> dd.login("robin").show('users.UsersOverview', limit=5)

    Usage in a Jinja template::

      {{ar.show('users.UsersOverview')}}

    Usage in an appy.pod template::

      do text from ar.show('users.UsersOverview')

    Note that this function either returns a string or prints to
    stdout and returns None, depending on the current renderer.


  .. method:: spawn(spec, **kwargs)

    Create a new ActionRequest using default values from this one and
    the action specified by `spec`.  

  .. method:: set_response(**kw)

    Set (some part of) the response to be sent when the action request
    finishes.  This does not yet respond anything, it is stored until
    the action has finished. The response might be overwritten by
    subsequent calls to `set_response`.

    Allowed keywords are:

    - ``message`` -- a string with a message to be shown to the user.

    - ``alert`` -- True to specify that the message is rather important
      and should alert and should be presented in a dialog box to be
      confirmed by the user.

    - ``success``
    - ``errors``
    - ``html``
    - ``rows``
    - ``data_record``
    - ``goto_record_id``
    - ``refresh``
    - ``refresh_all``
    - ``close_window``
    - ``xcallback``
    - ``open_url``
    - ``open_davlink_url``
    - ``info_message``
    - ``warning_message``
    - ``eval_js``

  .. method:: table2xhtml(self, header_level=None, **kw)
     
    Available only when the actor is a :class:`dd.AbstractTable`.

  .. method:: dump2html(self, tble, data_iterator, column_names=None):

    Available only when the actor is a :class:`dd.AbstractTable`.

    Render this table into an existing
    :class:`lino.utils.xmlgen.html.Table` instance.

  .. method:: goto_instance(self, obj, **kw)

    Ask the client to display a :term:`detail window` on the given
    record. The client might ignore this if Lino does not know a
    detail window.

    This is a utility wrapper around :meth:`set_response` which sets
    either `data_record` or a `record_id`.

    Usually `data_record`, except if it is a `file upload
    <https://docs.djangoproject.com/en/dev/topics/http/file-uploads/>`_
    where some mysterious decoding problems (:blogref`20120209`)
    force us to return a `record_id` which has the same visible
    result but using an additional GET.

    If the calling window is a detail on the same table, then it
    should simply get updated to the given record. Otherwise open a
    new detail window.

  .. method:: get_field_info(self, ar, column_names=None)

    Return a tuple (fields, headers, widths) which expresses which
    columns, headers and widths the user wants for this request. If
    `self` has web request info, checks for GET parameters cn, cw and
    ch (coming from the grid widget). Also apply the tables's
    :meth:`override_column_headers
    <dd.Actor.override_column_headers>` method.


