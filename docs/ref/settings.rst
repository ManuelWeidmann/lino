============
Settings API
============


.. setting:: SITE

Lino expects one important variable ``SITE`` in your :xfile:`settings.py`.
See :ref:`djangosite`.


Lino and the Django `settings.py` file
--------------------------------------

This section describes Lino-specific entries of the Django :xfile:`settings.py`.

.. setting:: LOGGING
.. setting:: LOGGING_CONFIG

Lino sets :setting:`LOGGING_CONFIG` to :func:`lino.utils.log.configure` 
which is our suggetion for a lightweight flexible 
logging configuration method. If you leave :setting:`LOGGING_CONFIG` 
unchanged, you can configure your logging preferences using the 
:setting:`LOGGING` setting. Some examples::

    LOGGING = dict(filename='/var/log/lino/system.log'),level='DEBUG')
    LOGGING = dict(filename=join(LINO.project_dir,'log','system.log'),level='DEBUG')
    LOGGING = dict(filename=None,level='DEBUG')


You don't need to use Lino's logging config. In that case, refer to
https://docs.djangoproject.com/en/dev/ref/settings/#logging-config


.. setting:: USE_L10N

See http://docs.djangoproject.com/en/dev/ref/settings/#use-l10n

.. setting:: LANGUAGE_CODE

See http://docs.djangoproject.com/en/dev/ref/settings/#language-code

.. setting:: ROOT_URL

See http://docs.djangoproject.com/en/dev/ref/settings/#root-url

.. setting:: DATABASES

  See http://docs.djangoproject.com/en/dev/ref/settings/#databases
  
.. setting:: MIDDLEWARE_CLASSES

  See http://docs.djangoproject.com/en/dev/ref/settings/#middleware_classes
  
.. setting:: LANGUAGES

  Used by :class:`lino.modlib.fields.LanguageField`.
  See http://docs.djangoproject.com/en/dev/ref/settings/#languages

.. setting:: ROOT_URLCONF

You'll set this to :mod:`lino.ui.extjs3.urls` and don't need to write 
any local html nor css.

We are also working on alternative user interfaces 
:mod:`lino.ui.extjs4.urls` and
:mod:`lino.ui.qx.urls`.


.. setting:: INSTALLED_APPS

Lino applications set Django's 
`INSTALLED_APPS <https://docs.djangoproject.com/en/dev/ref/settings/#installed-apps>`__
setting by calling the :setting:`get_installed_apps` method.


.. setting:: MEDIA_ROOT

  Used by FileSystemStorage.
  Used by :meth:`lino.ui.extjs.ext_ui.ExtUI.build_site_js` 
  and Printable to determine the location of the cache.

.. setting:: DEBUG

  See :blogref:`20100716`
  
.. setting:: SERIALIZATION_MODULES

See `Django doc <https://docs.djangoproject.com/en/1.3/ref/settings/#serialization-modules>`_ 
and :class:`north.Site`.


Obsolete Lino-specific settings
-------------------------------

.. setting:: USER_INTERFACES
  
   Lino-specific setting. See :blogref:`20100624`.

.. setting:: PROJECT_DIR

  (Replaced by :attr:`lino.Lino.project_dir`)

.. setting:: DATA_DIR

   Directory where local data gets stored. 
   On a Unix production system I suggest to set it to `/usr/local/lino`. 
   The development and demo configurations set it to ``os.path.join(PROJECT_DIR,'data')``.
   
.. setting:: MODEL_DEBUG

  If this is `True`, Lino will write more debugging info about the models and reports.

.. setting:: BYPASS_PERMS

   If this is `True`, Lino won't apply any user permission checks.
   


   
Environment variables
---------------------

.. envvar:: REMOTE_USER
  
  If :class:`lino.utils.simulate_remote.SimulateRemoteUserMiddleware` is active, this development server 
  will simulate HTTP authentication and set the `REMOTE_USER` meta attribute of every request to this name. 
  Without SimulateRemoteUserMiddleware active, this environment variable is not consulted.
  
  

