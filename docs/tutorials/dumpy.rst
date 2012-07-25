Writing your own demo fixtures
==============================

You have installed Lino on your server as explained in
:doc:`/admin/install`. 
You can see that data through your browser.
Now we suggest that you write your first local fixture.

Fixtures
--------

A fixture is a portion of data (a collection of data records 
in one or several tables) which can be loaded into a database.
Read more about fixtures in the `Providing initial data for models
<https://docs.djangoproject.com/en/dev/howto/initial-data/>`_
article of the Django documentation.

Django's documentation 
says that "fixtures can be written as XML, YAML, or JSON documents". 
Lino adds another format to this list: 
Python modules. 

`.py` fixtures are pure Python modules which define 
a function named ``objects`` which is expected to return 
(or `yield <http://stackoverflow.com/questions/231767/the-python-yield-keyword-explained>`_) 
the list of Model instances you want to create. A fictive minimal Example::

  from myapp.models import Foo
  def objects():
      yield Foo(name="First")
      yield Foo(name="Second")

If you are curious, read more details in :doc:`/topics/dumpy`.


More about the :mod:`initdb <lino.management.commands.initdb>` command
----------------------------------------------------------------------

Remember that we told you (in :doc:`/admin/install`) to "prepare your database" 
by running the command::

  python manage.py initdb std all_countries few_cities all_languages props demo 
  
The words "std", "all_countries", "few_cities" etc. are names of some *fixtures* 
included with Lino.
  
The :xfile:`manage.py` Python script is the standard Django interface to 
run management commands.
I you don't know what *Django management commands* are, 
please read this:
`django-admin.py and manage.py <https://docs.djangoproject.com/en/dev/ref/django-admin/>`_.

The :mod:`initdb <lino.management.commands.initdb>` 
command is a 
`custom management command <https://docs.djangoproject.com/en/dev/howto/custom-management-commands/>`_ 
provided by Lino.
It performs three actions in one:

- a flush of your database, removing *all existing tables* 
  (not only Django tables)
  from the database specified in your :xfile:`settings.py`,
 
- then runs Django's `syncdb` command to re-create all tables,
- and finally runs Django's `loaddata` command to load 
  the specified fixtures.

Removing all existing tables
may sound dangerous, but that's what we want when we have a 
:doc:`Python dump </topics/dumpy>` to restore our database.
Keep in mind that you should rather not let 
Lino and some other application share the same database.

The above line is roughly equivalent to::

  python manage.py flush
  python manage.py syncdb
  python manage.py loaddata std all_countries few_cities all_languages props demo 



Writing your own fixture
------------------------

Create a directory `fixtures` in your local project directory::

   mkdir ~/mypy/mysite/fixtures
   
Create a file `dumpy1.py` in that directory as the following.
But put your real name and data, this is your local file.

.. literalinclude:: dumpy1.py
    :linenos:
    
   
Try to apply this fixture::    

  $ python manage.py initdb dumpy1
  Gonna flush your database (myproject).
  Are you sure (y/n) ?y
  INFO Lino initdb ('dumpy1',) started on database myproject.
  INFO Lino version 1.1.11 using Python 2.7.1, Django 1.4 pre-alpha SVN-16280, 
  python-dateutil 1.4.1, Cheetah 2.4.4, docutils 0.7, PyYaml 3.08, 
  pyratemp (not installed), xhtml2pdf 3.0.32, ReportLab Toolkit 2.4, 
  appy.pod 0.6.6 (2011/04/26 20:50)
  No fixtures found.
  INFO Saved 2 instances from t:\hgwork\lino\docs\tutorials\dumpy1.py.
  Installed 1 object(s) from 1 fixture(s)
  INFO Lino initdb done ('dumpy1',) on database t:\data\luc\lino\dsbe\dsbe_test.db.


Second step
-----------

Since `.py` fixtures are normal Python modules, there are 
no limits to our phantasy when creating new objects.

A first thing that drops into mind is: there should be a more compact 
way to create many records of a same table. That's why 
:class:`lino.utils.instantiator.Instantiator` was written.
Here is the same fixture in a more compact way:

.. literalinclude:: dumpy2.py
    :linenos:


Third step
----------

Play around and try to add some more objects to your local demo database!


Fourth step
-----------

Have a look at the following fixture files

- :srcref:`few_countries </lino/modlib/countries/fixtures/few_countries.py>`
  and :srcref:`all_countries </lino/modlib/countries/fixtures/all_countries.py>`

- :srcref:`few_languages </lino/modlib/countries/fixtures/few_languages.py>`
  and :srcref:`all_languages </lino/modlib/countries/fixtures/all_languages.py>`

- :srcref:`few_cities </lino/modlib/countries/fixtures/few_cities.py>`
  and :srcref:`be </lino/modlib/countries/fixtures/be.py>`.

Play with them::

  python manage.py initdb std all_countries be few_languages props demo 
  python manage.py initdb std few_languages few_countries few_cities demo 
  ...

Conclusion
----------

Fixtures are good as long as 

- you are in "demo mode"
- you are preparing your local demo database
- you don't want your data to persistent forever
- there may be important changes in the database structure


Where to go now
---------------

Now we suggesst that your continue to read
:doc:`/tutorials/polls`