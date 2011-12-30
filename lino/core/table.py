## Copyright 2009-2011 Luc Saffre
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

import logging
logger = logging.getLogger(__name__)

import cgi
import os
import sys
import traceback
import codecs
import yaml
#~ import datetime
#import logging ; logger = logging.getLogger('lino.reports')
#~ import cPickle as pickle
#~ import pprint

from django.conf import settings
#~ from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst
from django.utils.encoding import force_unicode

from django.db import models
from django.db.models.query import QuerySet
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor
from django import forms
from django.conf.urls.defaults import patterns, url, include
from django.forms.models import modelform_factory
from django.forms.models import _get_foreign_key
#~ from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

#~ from dateutil import parser as dateparser

from django.http import HttpResponse
from django.utils.safestring import mark_safe


import lino
#~ from lino import layouts
from lino.core import fields
from lino.core import actions
from lino.utils import perms, menus, call_on_bases
from lino.utils.config import load_config_files, Configured
#~ from lino.core import datalinks
#~ from lino.core import boolean_texts
from lino.core import actors
#~ from lino.core import action_requests
from lino.ui import base

from lino.ui import requests as ext_requests

from lino.tools import resolve_model, resolve_field, get_app, full_model_name, get_field, UnresolvedModel
#~ from lino.utils.config import LOCAL_CONFIG_DIR
from lino.core.coretools import get_slave, get_model_report, get_data_elem

#~ from lino.modlib import field_choices

USER_MODEL = None


class ComputedColumn(object):
    def __init__(self,label,func):
        self.label = label
        self.func = func
        

def unused_parse_js_date(s,name):
    #~ v = dateparser.parse(s)
    #~ v = dateparser.parse(s,fuzzy=True)
    return datetime.date(*settings.LINO.parse_date(s))
    #~ print "parse_js_date %s : %r -> %s" % (name,s,v)
    #~ return v
    
    
def wildcard_data_elems(model):
    """Yields names that will be used as wildcard column_names of a Table.
    """
    meta = model._meta
    #~ for f in meta.fields: yield f.name
    #~ for f in meta.many_to_many: yield f.name
    #~ for f in meta.virtual_fields: yield f.name
    for f in meta.fields: 
        #~ if f.editable:
        if not isinstance(f,fields.VirtualField):
            if not getattr(f,'_lino_babel_field',False):
                yield f
    for f in meta.many_to_many: yield f
    for f in meta.virtual_fields: yield f
    # todo: for slave in self.report.slaves
  
    #~ for de in data_elems(self.model): yield de
      
    

def is_installed(app_label):
    if not '.' in app_label:
        app_label = '.' + app_label
    for s in settings.INSTALLED_APPS:
        if s.endswith(app_label):
            return True

def inject_field(model,name,field,doc=None):
    """
    Adds the given field to the given model.
    See also :doc:`/tickets/49`.
    """
    #~ model = resolve_model(model)
    if doc:
        field.__doc__ = doc
    model.add_to_class(name,field)
    return field



def fields_list(model,field_names):
    #~ return tuple([get_field(model,n) for n in field_names.split()])
    #~ if model.__name__ == 'Company':
        #~ print 20110929, [get_field(model,n) for n in field_names.split()]
    return [get_field(model,n).name for n in field_names.split()]


def summary_row(obj,ui,rr,**kw):
    m = getattr(obj,'summary_row',None)
    if m:
        return m(ui,rr,**kw)
    return ui.href_to(obj)
    #~ linkkw = {}
    #~ linkkw.update(fmt='detail')
    #~ url = ui.get_detail_url(obj,**linkkw)
    #~ return '<a href="%s">%s</a>' % (url,cgi.escape(force_unicode(obj)))
  

def summary(ui,rr,separator=', ',max_items=5,before='',after='',**kw):
    """
    Returns this report as a unicode string.
    
    :param max_items: don't include more than the specified number of items.
    """
    #~ if format is None:
        #~ def format(rr,obj):
            #~ return unicode(obj)
    s = u''
    n = 0
    for i in rr:
        if n:
            s += separator
        else:
            s += before
        n += 1
        s += summary_row(i,ui,rr,**kw)
        #~ s += i.summary_row(ui,rr,**kw)
        if n >= max_items:
            s += separator + '...' + after
            return s
    if n:
        return s + after
    return s

#~ def default_summary_row(obj,rr):
    #~ return u'<a href="%s" target="_blank">%s</a>' % (rr.get_request_url(str(obj.pk),fmt='detail'),unicode(obj))
    #~ return u'<span onClick="foo">%s</span>' % (ui.get_actor_url(self,str(obj.pk)),unicode(obj))
    #~ return u'<a href="#" onclick="Lino.foo">%s</a>' % unicode(obj)
        


def base_attrs(cl):
    #~ if cl is Table or len(cl.__bases__) == 0:
        #~ return
    #~ myattrs = set(cl.__dict__.keys())
    for b in cl.__bases__:
        for k in base_attrs(b):
            yield k
        for k in b.__dict__.keys():
            yield k


def add_quick_search_filter(qs,search_text):
    if not isinstance(qs,QuerySet): 
        # TODO: filter also simple lists 
        return qs
    q = models.Q()
    for field in qs.model._meta.fields:
        if isinstance(field,models.CharField):
            kw = {field.name+"__icontains": search_text}
            q = q | models.Q(**kw)
    return qs.filter(q)
    
    
def add_gridfilters(qs,gridfilters):
    """
    Converts a `filter` request in the format used by :extux:`Ext.ux.grid.GridFilters` into a 
    `Django field lookup <http://docs.djangoproject.com/en/1.2/ref/models/querysets/#field-lookups>`_
    on a :class:`django.db.models.query.QuerySet`.
    
    :param qs: the queryset to be modified.
    :param gridfilters: a list of dictionaries, each having 3 keys `field`, `type` and `value`.
    
    """
    if not isinstance(qs,QuerySet): 
        raise NotImplementedError('TODO: filter also simple lists')
    q = models.Q()
    for flt in gridfilters:
        field = get_field(qs.model,flt['field'])
        flttype = flt['type']
        kw = {}
        if flttype == 'string':
            if isinstance(field,models.CharField):
                kw[field.name+"__contains"] =  flt['value']
            elif isinstance(field,models.ForeignKey):
                search_field = getattr(field.rel.to,'grid_search_field',None)
                if search_field is None:
                    search_field = 'name'
                kw[field.name + "__%s__contains" % search_field] = flt['value']
            else:
                raise NotImplementedError(repr(flt))
        elif flttype == 'numeric':
            cmp = str(flt['comparison'])
            if cmp == 'eq': cmp = 'exact'
            kw[field.name+"__"+cmp] = flt['value']
        elif flttype == 'boolean':
            kw[field.name+"__equals"] = flt['value']
        elif flttype == 'date':
            v = datetime.date(*settings.LINO.parse_date(flt['value']))
            #~ v = parse_js_date(flt['value'],field.name)
            cmp = str(flt['comparison'])
            if cmp == 'eq': cmp = 'exact'
            kw[field.name+"__"+cmp] = v
            #~ print kw
        else:
            raise NotImplementedError(repr(flt))
        q = q & models.Q(**kw)
    return qs.filter(q)
        

def rc_name(rptclass):
    return rptclass.app_label + '.' + rptclass.__name__
    
def de_verbose_name(de):
    if isinstance(de,models.Field):
        return de.verbose_name
    return de.name

    
    
# TODO : move these global variables to LinoSite
master_reports = []
slave_reports = []
generic_slaves = {}
frames = []
rptname_choices = []

config_dirs = []

  
def register_frame(frm):
    frames.append(frm)
    
def register_report(rpt):
    #~ logger.debug("20111113 register_report %s", rpt.actor_id)
    #rptclass.app_label = rptclass.__module__.split('.')[-2]
    if rpt.typo_check:
        myattrs = set(rpt.__class__.__dict__.keys())
        for attr in base_attrs(rpt.__class__):
            myattrs.discard(attr)
        if len(myattrs):
            logger.warning("%s defines new attribute(s) %s", rpt.__class__, ",".join(myattrs))
    if rpt.model is None:
        #~ logger.debug("20111113 %s is an abstract report", rpt)
        return
        
    #~ if rpt.model._meta.abstract:
        
    #~ rptname_choices.append((rpt.actor_id, rpt.get_label()))
    rptname_choices.append(rpt.actor_id)
    
    if rpt.master is None:
        if not rpt.model._meta.abstract:
            master_reports.append(rpt)
        if not rpt.filter and not rpt.known_values and rpt.use_as_default_report:
            #~ logger.info("register %s : model_report for %s", rpt.actor_id, full_model_name(rpt.model))
            rpt.model._lino_model_report = rpt
    elif rpt.master is ContentType:
        #~ logger.debug("register %s : generic slave for %r", rpt.actor_id, rpt.master_key)
        generic_slaves[rpt.actor_id] = rpt
    else:
        slave_reports.append(rpt)

    
    
def discover():
    """
    - Each model can receive a number of "slaves". 
      Slaves are reports whose data depends on an instance of another model (their master).
      
    - For each model we want to find out the "model report" ot "default report".
      The "choices report" for a foreignkey field is also currently simply the pointed model's
      model_report.
      `_lino_model_report`

    """
              
    logger.info("Analyzing Reports...")
    #~ logger.debug("20111113 Register Table actors...")
    for rpt in actors.actors_list:
        if isinstance(rpt,Table) and rpt.__class__ is not Table:
            register_report(rpt)
        if isinstance(rpt,Frame) and rpt.__class__ is not Frame:
            register_frame(rpt)
            
    logger.debug("Instantiate model reports...")
    for model in models.get_models():
        """Not getattr but __dict__.get because of the mixins.Listings trick."""
        rpt = model.__dict__.get('_lino_model_report',None)
        #~ rpt = getattr(model,'_lino_model_report',None)
        #~ logger.debug('20111113 %s._lino_model_report = %s',model,rpt)
        if rpt is None:
            rpt = report_factory(model)
            register_report(rpt)
            model._lino_model_report = rpt
            
            
    logger.debug("Analyze %d slave reports...",len(slave_reports))
    for rpt in slave_reports:
        rpt.master = resolve_model(rpt.master)
        slaves = getattr(rpt.master,"_lino_slaves",None)
        if slaves is None:
            slaves = {}
            rpt.master._lino_slaves = slaves
        slaves[rpt.actor_id] = rpt
        #~ logger.debug("20111113 %s: slave for %s",rpt.actor_id, rpt.master.__name__)
    #~ logger.debug("Assigned %d slave reports to their master.",len(slave_reports))
        
    #~ logger.debug("Setup model reports...")
    #~ for model in models.get_models():
        #~ model._lino_model_report.setup()
        
    #~ logger.debug("Instantiate property editors...")
    #~ for model in models.get_models():
        #~ pw = ext_elems.PropertiesWindow(model)
        #~ model._lino_properties_window = pw
            
    #~ logger.debug("reports.setup() done")
    global USER_MODEL
    USER_MODEL = resolve_model(settings.LINO.user_model)



class StaticText:
    def __init__(self,text):
        self.text = text
        
#~ class Picture:
    #~ pass
    
#~ class DataView:
    #~ def __init__(self,tpl):
        #~ self.xtemplate = tpl
        

class Calendar(actions.OpenWindowAction):
    label = _("Calendar")
    name = 'grid' # because...
    default_format = 'html'
    
    def __init__(self,actor,*args,**kw):
        self.actor = actor # actor who offers this action
        self.can_view = perms.always # actor.can_view
        super(Calendar,self).__init__(*args,**kw)
        
    def __str__(self):
        return str(self.actor)+'.'+self.name
    

class ReportAction(actions.Action):
  
    def __init__(self,report,*args,**kw):
        self.actor = report # actor who offers this action
        self.can_view = report.can_view
        super(ReportAction,self).__init__(*args,**kw)
        
    def unused_request(self,ui=None,request=None,*args,**kw):
        ar = TableRequest(ui,self.actor,request,self,**kw)
        #~ ar.setup(**kw)
        return ar
        #~ return self.get_handle(ui).request(**kw)
      
        #~ return self.actor.request(self,*args,**kw)
        
    def get_button_label(self):
        if self is self.actor.default_action:
            return self.label 
        else:
            return u"%s %s" % (self.label,self.actor.label)
            
    #~ def get_list_title(self,rh):
    def get_action_title(self,rr):
        return rr.get_title()
        
    def __str__(self):
        return str(self.actor)+'.'+self.name
        
#~ class JsonAction(ReportAction):
    #~ name = 'json'


class GridEdit(ReportAction,actions.OpenWindowAction):
  
    callable_from = tuple()
    name = 'grid'
    
    def __init__(self,rpt):
        self.label = rpt.button_label or rpt.label
        ReportAction.__init__(self,rpt)


class ShowDetailAction(ReportAction,actions.OpenWindowAction):
    callable_from = (GridEdit,)
    #~ show_in_detail = False
    #~ needs_selection = True
    name = 'detail'
    label = _("Detail")
    
    #~ def get_elem_title(self,elem):
        #~ return _("%s (Detail)")  % unicode(elem)
    
        
class InsertRow(ReportAction,actions.OpenWindowAction):
    callable_from = (GridEdit,ShowDetailAction)
    name = 'insert'
    #~ label = _("Insert")
    label = _("New")
    key = actions.INSERT # (ctrl=True)
    #~ needs_selection = False
    
    def get_action_title(self,rr):
        return _("Insert into %s") % force_unicode(rr.get_title())

class DuplicateRow(ReportAction,actions.OpenWindowAction):
    callable_from = (GridEdit,ShowDetailAction)
    name = 'duplicate'
    label = _("Duplicate")

class RowAction(actions.Action):
    callable_from = (GridEdit,ShowDetailAction)
    
    def disabled_for(self,obj,request):
        return False
    #~ needs_selection = False
    #~ needs_validation = False
    #~ def before_run(self,ar):
        #~ if self.needs_selection and len(ar.selected_rows) == 0:
            #~ return _("No selection. Nothing to do.")
            
            
class UpdateRowAction(RowAction):
    pass
    
class DeleteSelected(RowAction):
    #~ needs_selection = True
    label = _("Delete")
    name = 'delete'
    key = actions.DELETE # (ctrl=True)
    #~ client_side = True
    
        
class SubmitDetail(actions.Action):
    #~ name = 'submit'
    label = _("Save")
    callable_from = (ShowDetailAction,)
    
class SubmitInsert(SubmitDetail):
    #~ name = 'submit'
    label = _("Save")
    #~ label = _("Insert")
    callable_from = (InsertRow,)
        


      
class ReportHandle(base.Handle): 
    
    def __init__(self,ui,report):
        #~ logger.debug('20111113 ReportHandle.__init__(%s)',report)
        assert isinstance(report,Table)
        self.report = report
        #~ self.data_elems = report.data_elems
        #~ self.get_data_elem = report.get_data_elem
        self._layouts = None
        #~ actors.ActorHandle.__init__(self,report)
        #~ datalinks.DataLink.__init__(self,ui)
        #~ self.ui = ui
        base.Handle.__init__(self,ui)
        if self.report.model is not None:
            if not self.report.model._meta.abstract:
                if ui is not None:
                    self.list_layout = ListLayoutHandle(self,
                        ListLayout('main = '+self.report.column_names),
                        hidden_elements=self.report.hidden_columns)
                #~ self.content_type = ContentType.objects.get_for_model(self.report.model).pk
        
  
    def __str__(self):
        return str(self.report) + 'Handle'
            
    def setup_layouts(self):
        if self._layouts is not None:
            return
        self._layouts = [ self.list_layout ] 
        #~ if self.report.model is not None:
            #~ self._layouts += [ 
                #~ LayoutHandle(self.ui,self.report.model,dtl) 
                #~ for dtl in self.report.detail_layouts ]
              
    def get_actor_url(self,*args,**kw):
        return self.ui.get_actor_url(self.report,*args,**kw)
        
    def submit_elems(self):
        return []
        
    #~ def get_layout(self,i):
        #~ self.setup_layouts()
        #~ return self._layouts[i]
        
    #~ def get_used_layouts(self):
        #~ self.setup_layouts()
        #~ return self._layouts
        
    #~ def get_detail_layouts(self):
        #~ if self.model._lino_detail is None:
            #~ return []
        #~ dh = self.model._lino_detail.get_handle(self.ui)
        #~ return dh.layouts
        
    #~ def get_detail_layouts(self):
        #~ self.setup_layouts()
        #~ return self._layouts[1:]
        
    def get_list_layout(self):
        self.setup_layouts()
        return self._layouts[0]
        
    def get_columns(self):
        layout = self.get_list_layout()
        #~ print 20110315, layout._main.columns
        return layout._main.columns
        
    #~ def get_absolute_url(self,*args,**kw):
        #~ return self.ui.get_report_url(self,*args,**kw)
        
    #~ def data_elems(self):
        #~ for de in self.report.data_elems(): yield de
    #~ def get_data_elem(self,name):
        #~ return get_data_elem(self.report.model,name)
        
    def get_slaves(self):
        return [ sl.get_handle(self.ui) for sl in self.report._slaves ]
            
    def get_action(self,name):
        return self.report.get_action(name)
    def get_actions(self,*args,**kw):
        return self.report.get_actions(*args,**kw)
        
        
    #~ def request(self,*args,**kw):
        #~ ar = ReportActionRequest(self.ui,self.report.list_action)
        #~ ar.setup(*args,**kw)
        #~ return ar
        
    def update_detail(self,tab,desc):
        #~ raise Exception("Not yet fully converted to Lino 1.3.0")
        old_dl = self.report.get_detail().layouts[tab]
        dtl = DetailLayout(desc,old_dl.filename,old_dl.cd)
        self.report.get_detail().layouts[tab] = dtl
        #~ dh = dtl.get_handle(self.ui)
        #~ self._layouts[tab+1] = LayoutHandle(self.ui,self.report.model,dtl)
        self.ui.setup_handle(self)
        #~ self.report.save_config()
        dtl.save_config()

class InvalidRequest(Exception):
    pass


class ActionRequest(object):
    def __init__(self,ui,action):
        self.ui = ui
        self.action = action
        
    def request2kw(self,ui,**kw):
        return kw
  

class TableRequest(ActionRequest):
    """
    An Action Request on a given Table.
    """
    limit = None
    offset = None
    master_instance = None
    master = None
    instance = None
    create_rows = None
    extra = None
    layout = None
    
    sort_column = None
    sort_direction = None
    
    def __init__(self,ui,report,request,action,*args,**kw):
        if not isinstance(report,Table):
            raise Exception("Expected a Table instance, got %r" % report)
        #~ reports.ReportActionRequest.__init__(self,rh.ui,rh.report,action)
        ActionRequest.__init__(self,ui,action)
        self.report = report
        self.ah = report.get_handle(ui)
        #~ self.ah = rh
        self.request = request
        #~ self.store = rh.store
        #~ if request is None:
            #~ self.user = None
        #~ else:
            #~ kw = self.parse_req(request,self.ah,**kw)
        if request is not None:
            kw = self.parse_req(request,self.ah,**kw)
        self.setup(*args,**kw)
    
    
    def parse_req(self,request,rh,**kw):
        master = kw.get('master',self.report.master)
        if master is ContentType or master is models.Model:
            mt = request.REQUEST.get(ext_requests.URL_PARAM_MASTER_TYPE)
            try:
                master = kw['master'] = ContentType.objects.get(pk=mt).model_class()
            except ContentType.DoesNotExist,e:
                pass
                #~ master is None
                #~ raise ContentType.DoesNotExist("ContentType %r does not exist." % mt)
                
            #~ print kw
        if master is not None and not kw.has_key('master_instance'):
            pk = request.REQUEST.get(ext_requests.URL_PARAM_MASTER_PK,None)
            #~ print '20100406a', self.report,URL_PARAM_MASTER_PK,"=",pk
            #~ if pk in ('', '-99999'):
            if pk == '':
                pk = None
            if pk is None:
                kw['master_instance'] = None
            else:
                try:
                    kw['master_instance'] = master.objects.get(pk=pk)
                except ValueError,e:
                    raise Exception("Invalid primary key %r for %s",pk,master.__name__)
                except master.DoesNotExist,e:
                    # todo: ReportRequest should become a subclass of Dialog and this exception should call dlg.error()
                    raise Exception("There's no %s with primary key %r" % (master.__name__,pk))
            #~ print '20100212', self #, kw['master_instance']
        #~ print '20100406b', self.report,kw
        
        if settings.LINO.use_filterRow:
            exclude = dict()
            for f in rh.store.fields:
                if f.field:
                    filterOption = request.REQUEST.get('filter[%s_filterOption]' % f.field.name)
                    if filterOption == 'empty':
                        kw[f.field.name + "__isnull"] = True
                    elif filterOption == 'notempty':
                        kw[f.field.name + "__isnull"] = False
                    else:
                        filterValue = request.REQUEST.get('filter[%s]' % f.field.name)
                        if filterValue:
                            if not filterOption: filterOption = 'contains'
                            if filterOption == 'contains':
                                kw[f.field.name + "__icontains"] = filterValue
                            elif filterOption == 'doesnotcontain':
                                exclude[f.field.name + "__icontains"] = filterValue
                            else:
                                print "unknown filterOption %r" % filterOption
            if len(exclude):
                kw.update(exclude=exclude)
        if settings.LINO.use_gridfilters:
            filter = request.REQUEST.get(ext_requests.URL_PARAM_GRIDFILTER,None)
            if filter is not None:
                filter = json.loads(filter)
                kw['gridfilters'] = [ext_requests.dict2kw(flt) for flt in filter]
                
        kw.update(self.report.known_values)
        for fieldname, default in self.report.known_values.items():
            v = request.REQUEST.get(fieldname,None)
            if v is not None:
                kw.update(fieldname=v)
        
        quick_search = request.REQUEST.get(ext_requests.URL_PARAM_FILTER,None)
        if quick_search:
            kw.update(quick_search=quick_search)
        offset = request.REQUEST.get(ext_requests.URL_PARAM_START,None)
        if offset:
            kw.update(offset=int(offset))
        limit = request.REQUEST.get(ext_requests.URL_PARAM_LIMIT,None)
        if limit:
            kw.update(limit=int(limit))
        #~ else:
            #~ kw.update(limit=self.report.page_length)
            
        
        sort = request.REQUEST.get(ext_requests.URL_PARAM_SORT,None)
        if sort:
            self.sort_column = sort
            sort_dir = request.REQUEST.get(ext_requests.URL_PARAM_SORTDIR,'ASC')
            if sort_dir == 'DESC':
                sort = '-'+sort
                self.sort_direction = 'DESC'
            kw.update(order_by=[sort])
        
        kw.update(user=request.user)
        #~ user = request.user
        #~ if user is not None and user.is_superuser:
        #~ if True:
        username = request.REQUEST.get(ext_requests.URL_PARAM_SUBST_USER,None)
        if username:
            try:
                kw.update(subst_user=USER_MODEL.objects.get(username=username))
            except USER_MODEL.DoesNotExist, e:
                pass
        #~ kw.update(user=user)
        
        kw = rh.report.parse_req(request,**kw)
        
        return kw
        
      
    def setup(self,
            master=None,
            master_instance=None,
            master_id=None,
            offset=None,limit=None,
            layout=None,
            user=None,
            subst_user=None,
            filter=None,
            create_rows=None,
            quick_search=None,
            gridfilters=None,
            order_by=None,
            exclude=None,
            extra=None,
            known_values=None,
            #~ expand_memos=None,
            #~ selected_rows=None,
            **kw):
        if user is not None and not self.report.can_view.passes(user):
            msg = _("User %(user)s cannot view %(report)s.") % dict(user=user,report=self.report)
            raise InvalidRequest(msg)
        self.user = user
        self.subst_user = subst_user
        self.filter = filter
        #~ if isinstance(self.action,GridEdit):
            #~ self.expand_memos = expand_memos or self.report.expand_memos
        self.quick_search = quick_search
        self.gridfilters = gridfilters
        self.order_by = order_by
        self.exclude = exclude or self.report.exclude
        self.extra = extra
        #~ self.known_values = known_values or self.report.known_values
        #~ if self.report.known_values:
        for k,v in self.report.known_values.items():
            kw.setdefault(k,v)
        if known_values:
            kw.update(known_values)
        #~ if self.report.__class__.__name__ == 'SoftSkillsByPerson':
            #~ logger.info("20111223 %r %r", kw, self.report.known_values)
        self.known_values = kw

        #~ if selected_rows is not None:
            #~ self.selected_rows = selected_rows
        
        if master is None:
            master = self.report.master
            # master might still be None
        self.master = master
        
        #~ if self.report.params:
            #~ raise Exception("%s.params is %r" % (self.report,self.report.params))
        #~ kw.update(self.report.params)
        #~ self.params = kw
        
        if master_id is not None:
            assert master_instance is None
            master_instance = self.master.objects.get(pk=master_id)
            
        self.create_kw = self.report.get_create_kw(master_instance)
        self.master_instance = master_instance
        if self.create_rows is None:
            if create_rows is None:
                if self.create_kw is None:
                    create_rows = 0
                #~ elif self.user is not None and self.report.can_add.passes(self.user):
                elif self.report.can_add.passes(self.user):
                    create_rows = 1
                else:
                    create_rows = 0
            self.create_rows = create_rows
        if self.ui is not None:
            if layout is None:
                layout = self.ah._layouts[self.report.default_layout]
            else:
                layout = self.ah._layouts[layout]
            self.layout = layout
        self.report.setup_request(self)
        self.queryset = self.get_queryset()
        #~ self.setup_queryset()
        #~ logger.debug(unicode(self))
        # get_queryset() may return a list
        """
        TODO: 
        Note that `total_count` is looked up 
        *before* `offset` and `limit` are set.
        That's a pity because it creates a database lookup
        even if the TableRequest is being instantiated with 
        the only purpose of generating an url.
        """
        if isinstance(self.queryset,models.query.QuerySet):
            self.total_count = self.queryset.count()
        else:
            self.total_count = len(self.queryset)
        
        #~ if limit is None:
            #~ limit = self.report.page_length
            
        """
        Table.page_length is not a default value for ReportRequest.limit
        For example CSVReportRequest wants all rows.
        """
        if offset is not None:
            self.queryset = self.queryset[offset:]
            self.offset = offset
            
        if limit is not None:
            self.queryset = self.queryset[:limit]
            self.limit = limit
            
        self.page_length = self.report.page_length
        
        
    def __str__(self):
        return self.__class__.__name__ + '(' + self.report.actor_id + ",%r,...)" % self.master_instance

    def get_queryset(self):
        # overridden by ChoicesReportRequest
        return self.report.get_request_queryset(self)
        #~ return self.report.get_queryset(master_instance=self.master_instance,**kw)
        
    def __iter__(self):
        return self.queryset.__iter__()
        
    def get_base_filename(self):
        return str(self.report)
        #~ s = self.get_title()
        #~ return s.encode('us-ascii','replace')
        
    def __getitem__(self,*args):
        return self.queryset.__getitem__(*args)
        
    def __len__(self):
        return self.queryset.__len__()
        
    def create_instance(self,**kw):
        if self.create_kw:
            kw.update(self.create_kw)
        #logger.debug('%s.create_instance(%r)',self,kw)
        if self.known_values:
            kw.update(self.known_values)
        obj = self.report.create_instance(self,**kw)
        #~ if self.known_values is not None:
            #~ self.ah.store.form2obj(self.known_values,obj,True)
            #~ for k,v in self.known_values:
                #~ field = self.model._meta.get_field(k) ...hier
                #~ kw[k] = v
        return obj
        
    def get_user(self):
        return self.subst_user or self.user
        
    def get_action_title(self):
        return self.action.get_action_title(self)
        
    def get_title(self):
        return self.report.get_title(self)
        
    def render_to_dict(self):
        return self.action.render_to_dict(self)
        
    #~ def row2dict(self,row,d):
        #~ # overridden in extjs.ext_requests.ViewReportRequest
        #~ return self.report.row2dict(row,d)

    def get_request_url(self,*args,**kw):
        return self.ui.get_request_url(self,*args,**kw)

    def spawn_request(self,rpt,**kw):
        #~ rh = rpt.get_handle(self.ui)
        kw.update(user=self.user)
        #~ return ViewReportRequest(None,rh,rpt.default_action,**kw)
        return self.__class__(self.ui,rpt,None,rpt.default_action,**kw)
        
    def request2kw(self,ui,**kw):
        #~ if self.report.__class__.__name__ == 'MyPersonsByGroup':
            #~ print 20111223, self.known_values
        if self.subst_user is not None:
            kw[ext_requests.URL_PARAM_SUBST_USER] = self.subst_user.username
            
        if self.known_values:
            #~ kv = dict()
            for k,v in self.known_values.items():
                if self.report.known_values.get(k,None) != v:
                    kw[k] = v
                
            #~ kw[ext_requests.URL_PARAM_KNOWN_VALUES] = self.known_values
        if self.quick_search:
            kw[ext_requests.URL_PARAM_FILTER] = self.quick_search
        if self.master_instance is not None:
            kw[ext_requests.URL_PARAM_MASTER_PK] = self.master_instance.pk
            mt = ContentType.objects.get_for_model(self.master_instance.__class__).pk
            kw[ext_requests.URL_PARAM_MASTER_TYPE] = mt
        return kw
        
    def confirm(self,step,*messages):
        if self.request.REQUEST.get(ext_requests.URL_PARAM_ACTION_STEP,None) == str(step):
            return
        raise actions.ConfirmationRequired(step,messages)


#~ class IterActionRequest(actions.ActionRequest)
    #~ def __init__(self,ui,iter,action):
        #~ self.iter = iter
        #~ actions.ActionRequest.__init__(self,ui,action)
        
        
def has_fk(rr,name):
    if isinstance(rr,TableRequest):
        return rr.report.master_key == name
    return False

        
def model2report(m):
    def f(self,obj,request):
        return m(obj,request)
        #~ return getattr(obj,name)(request)
    return f


class FrameHandle(base.Handle): 
    def __init__(self,ui,frame):
        assert isinstance(frame,Frame)
        self.report = frame
        base.Handle.__init__(self,ui)

    def get_actions(self,*args,**kw):
        return self.report.get_actions(*args,**kw)

class Frame(actors.Actor): 
  
    _handle_class = FrameHandle
    default_action_class = None
    
    def __init__(self):
        logger.info("%s.__init__()",self.__class__)
        #~ if not self.__class__ is Frame:
        if self.default_action_class:
            self.default_action = self.default_action_class(self)
        if not self.label:
            self.label = self.default_action.label
            #~ self.default_action.actor = self
        super(Frame,self).__init__()
  
    def do_setup(self):
        if self.default_action:
            self.add_action(self.default_action)
        
class Table(actors.Actor): #,base.Handled):
    """
    
    A Table is the definition of a tabular data view, 
    usually displayed in a Grid (but it's up to the user 
    interface to decide how to implement this).
    A Table definition has attributes
    like `filter` and `sort_order` 
    which it forwards to the QuerySet 
    and which we sometimes call "horizontal layout" 
    because they influence the rows to be selected.
    But it usually also has a "vertical layout", 
    for example the `column_names` attribute.

    """
    #~ default_action_class = GridEdit
    _handle_class = ReportHandle
    #~ _handle_selector = base.UI
    #~ params = {}
    field = None
    
    #~ hide_details = []
    #~ """
    #~ A list of base classes whose `.dtl` files should not be loaded for this report.
    #~ """
    
    base_queryset = None 
    "See :meth:`Table.get_queryset`"
    
    #~ default_params = {}
    """See :doc:`/blog/2011/0701`.
    """
    
    model = None
    """
    The model on which this table iterates.
    """
    
    use_as_default_report = True
    """
    Set this to False if this Table should not become the model's default table.
    """
    
    order_by = None
    
    expand_memos = False
    """
    (No longer used; see :doc:`/tickets/44`). 
    Whether multi-line text fields in Grid views should be expanded in by default or not.
    """
    
    extra = None
    """
    Examples::
    
      extra = dict(select=dict(lower_name='lower(name)'))
      # (or if you prefer:) 
      # extra = {'select':{'lower_name':'lower(name)'},'order_by'=['lower_name']}
      
    
    List of SQL functions and which RDBMS supports them:
    http://en.wikibooks.org/wiki/SQL_Dialects_Reference/Functions_and_expressions/String_functions
    
    """
    
    filter = None
    """
    If specified, this must be a dict of (fieldname -> value) pairs which 
    will be used as a filter.
    
    Unlike :attr:`known_values`, this can use the full range of 
    Django's `field lookup methods 
    <https://docs.djangoproject.com/en/dev/topics/db/queries/#field-lookups>`_
    
    Note that if the user can create rows in a filtered table, 
    you should make sure that new records satisfy your filter condition 
    by default, otherwise you can get surprising behaviour if the user 
    creates a new row.
    If your filter consists of simple static values on some known field, 
    then you'll prefer to use :attr:`known_values` instead of :attr:`filter.`
    """
    exclude = None
    title = None
    column_names = '*'
    #~ hide_columns = None
    hidden_columns = frozenset()
    form_class = None
    master = None
    
    master_key = None
    """
    The name of the ForeignKey field of this report's model that points to it's master.
    Setting this will turn the report into a slave report.
    """
    
    help_url = None
    #master_instance = None
    
    page_length = 30
    """
    Number of rows to display per page.
    """
    
    cell_edit = True 
    """
    `True` to use ExtJS CellSelectionModel, `False` to use RowSelectionModel.
    """
    
    #~ date_format = lino.DATE_FORMAT_EXTJS
    #~ boolean_texts = boolean_texts
    boolean_texts = boolean_texts = (_('Yes'),_('No'),' ')
    
    can_view = perms.always
    can_add = perms.is_authenticated
    can_change = perms.is_authenticated
    can_config = perms.is_staff
    
    show_prev_next = True
    
    #~ default_action = GridEdit
    default_layout = 0
    
    typo_check = True
    """
    True means that Lino shoud issue a warning if a subclass 
    defines any attribute that did not exist in the base class.
    Usually such a warning means that there is something wrong.
    """
    
    #~ url = None
    
    known_values = {}
    """
    A `dict` of `fieldname` -> `value` pairs that specify "known values".
    Requests will automatically be filtered to show only existing records 
    with those values.
    This is like :attr:`filter`, but 
    new instances created in this Table will automatically have 
    these values set.
    
    """
    
    #~ use_layouts = True
    
    button_label = None
    
    active_fields = []
    """A list of field names that are "active" (cause a save and 
    refresh of a Detail or Insert form).
    """
    
    #~ detail_layouts = []
    
    show_slave_grid = True
    """
    How to display this report when it is a slave in a Detail. 
    `True` (default) to render as a grid. 
    `False` to render as a HtmlBoxPanel with a summary.
    Example: :class:`links.LinksByOwner`
    """
    
    grid_configs = []
    """
    Will be filled during :meth:`lino.core.table.Table.do_setup`. 
    """
    
    disabled_fields = None
    """
    Return a list of field names that should not be editable 
    for the specified `obj` and `request`.
    
    If defined in the Table, this must be a method that accepts 
    two arguments `request` and `obj`::
    
      def disabled_fields(self,obj,request):
          ...
          return []
    
    If not defined in a subclass, the report will look whether 
    it's model has a `disabled_fields` method expecting a single 
    argument `request` and install a wrapper to this model method.
    See also :doc:`/tickets/2`.
    """
    
    handle_uploaded_files = None
    """
    Handler for uploaded files.
    Same remarks as for :attr:`disabled_fields`.
    """
    
    disable_editing = None
    """
    Return `True` if the record as a whole should be read-only.
    Same remarks as for :attr:`disabled_fields`.
    """
    
    has_navigator = True
    """
    Whether a Detail Form should have navigation buttons.
    This option is False in :class:`lino.SiteConfigs`.
    """
    
    detail_action = None
    
    computed_columns = dict()
    
    def __init__(self):
        if self.model is None:
            if self.base_queryset is not None:
                self.model = self.base_queryset.model
            # raise Exception(self.__class__)
        else:
            self.model = resolve_model(self.model,self.app_label)
            
        if isinstance(self.model,UnresolvedModel):
            self.model = None
            
        if self.model is not None:
            # 20110822 : a report now always gets the app_label of its model
            # you cannot set this yourself in a subclass
            # because otherwise it gets complex when inheriting reports from other app_labels
            # 20110912 Cancelled change 20110822 because PersonsByOffer 
            # should clearly get app_label 'jobs' and not 'contacts'.
            #~ if self.app_label is None:
            #~ if not self.__dict__.has_key('app_label'):
                # Figure out the app_label by looking one level up.
                # For 'django.contrib.sites.models', this would be 'sites'.
                #~ m = sys.modules[self.__module__]
                #~ self.app_label = m.__name__.split('.')[-2]
                #~ self.app_label = self.model._meta.app_label
            if self.label is None:
                #~ self.label = capfirst(self.model._meta.verbose_name_plural)
                self.label = self.init_label()
            
        #~ logger.debug("Table.__init__() %s", self)
        actors.Actor.__init__(self)
        #~ base.Handled.__init__(self)
        
        if self.model is not None:
          
            for name in ('disabled_fields',
                         'handle_uploaded_files', 
                         'disable_editing'):
                if getattr(self,name) is None:
                    m = getattr(self.model,name,None)
                    if m is not None:
                        #~ logger.debug('20111113 Install model method %s.%s to %s',self.model.__name__,name,self)
                        setattr(self.__class__,name,model2report(m))
                        
            if self.master_key:
                #~ assert self.model is not None, "%s has .master_key but .model is None" % self
                #~ self.master = resolve_model(self.master,self.app_label)
                try:
                    fk, remote, direct, m2m = self.model._meta.get_field_by_name(self.master_key)
                    assert direct
                    assert not m2m
                    master = fk.rel.to
                except models.FieldDoesNotExist,e:
                    #~ logger.debug("FieldDoesNotExist in %r._meta.get_field_by_name(%r)",self.model,self.master_key)
                    master = None
                    for vf in self.model._meta.virtual_fields:
                        if vf.name == self.master_key:
                            fk = vf
                            master = ContentType
                if master is None:
                    raise Exception("%s : no master for master_key %r in %s" % (
                        self,self.master_key,self.model.__name__))
                self.master = master
                self.fk = fk
        #~ else:
            #~ assert self.master is None
        
        #~ self.default_action = self.default_action_class(self)
        self.default_action = GridEdit(self)
        #~ self.default_elem_action = ShowDetailAction(self)
        #~ self.list_action = ListAction(self)
        
        if self.order_by is not None:
            if not isinstance(self.order_by,(list,tuple)):
                raise Exception("%s.order_by is %r (must be a list or tuple)" % (self,self.order_by))
            if False: 
              # good idea, but doesn't yet work for foreign fields, 
              # e.g. order_by = ['content_type__app_label']
              for fieldname in self.order_by:
                  if fieldname.startswith('-'):
                      fieldname = fieldname[1:]
                  try:
                      fk, remote, direct, m2m = self.model._meta.get_field_by_name(fieldname)
                      assert direct
                      assert not m2m
                  except models.FieldDoesNotExist,e:
                      raise Exception("Unknown fieldname %r in %s.order_by" % (fieldname,self))
        
        
    @classmethod
    def spawn(cls,suffix,**kw):
        kw['app_label'] = cls.app_label
        return type(cls.__name__+str(suffix),(cls,),kw)
        
    def init_label(self):
        return self.model._meta.verbose_name_plural
        
    def column_choices(self):
        return [ de.name for de in wildcard_data_elems(self.model) ]
          
    def parse_req(self,request,**kw):
        return kw
    
    def do_setup(self):
      
        #~ filename = self.get_grid_config_file()
        self.grid_configs = []
        
        def loader(content,cd,filename):
            data = yaml.load(content)
            gc = GridConfig(self,data,filename,cd)
            self.grid_configs.append(gc)
            
        load_config_files(loader,'%s.*gc' % self)
            
        
        #~ if os.path.exists(filename):
            #~ logger.info("Loading %s...",filename)
            #~ try:
                #~ d = yaml.load(codecs.open(filename,encoding='utf-8').read())
                #~ if d is not None:
                    #~ must_save = self.validate_grid_config(d)
                    #~ self.grid_configs = d['grid_configs']
                    #~ if must_save:
                        #~ msg = self.save_grid_config()
                        #~ logger.debug(msg)
            #~ except Exception,e:
                #~ logger.warning("Exception while loading %s : %s",filename,e)
                #~ logger.exception(e)
          
        if self.model is not None:
                
            if hasattr(self.model,'_lino_slaves'):
                self._slaves = self.model._lino_slaves.values()
            else:
                self._slaves = []
                
        #~ self.setup_detail_layouts()
        self.set_actions([])
        self.setup_actions()
        self.add_action(self.default_action)
                
        if self.button_label is None:
            self.button_label = self.label
            
        if self.model is not None:
            m = getattr(self.model,'setup_report',None)
            if m:
                m(self)
            #~ call_on_bases(self.model,'setup_report',self)
        
    def disabled_actions(self,obj,request):
        l = []
        for a in self.get_actions():
            if isinstance(a,RowAction):
                if a.disabled_for(obj,request):
                    l.append(a.name)
        return l
        
    def disable_delete(self,obj,request):
        """
        Return either `None` if the given `obj` *is allowed* 
        to be deleted by `request`,
        or a string with a message explaining why, if not.
        """
        return self.model._lino_ddh.disable_delete(obj,request)
        
    def setup_actions(self):
        if self.model is not None:
            #~ if len(self.detail_layouts) > 0:
            if self.model._lino_detail:
                self.detail_action = ShowDetailAction(self)
                self.add_action(self.detail_action)
                self.add_action(SubmitDetail())
                self.add_action(InsertRow(self))
                #~ self.add_action(actions.DuplicateRow(self))
                self.add_action(SubmitInsert())
                    
            self.add_action(DeleteSelected())
            
            #~ if hasattr(self.model,'get_image_url'):
                #~ self.add_action(actions.ImageAction())
        
      
    def unused_setup_detail_layouts(self):
        """
        Yield all detail tabs for this report.
        Each detail tab corresponds to a :xfile:`.dtl` file).
        Detail tabs of inherited models come *first*.
        Example: CouseProvider(Company) will yield first all 
        tabs found for Company, then those for CourseProvider.
        """
        self.detail_layouts = []
        
        #~ for b in self.__class__.__bases__:
            #~ for dtl in br.detail_layouts:
                #~ self.detail_layouts.append(dtl)
                
        if self.model is None:
            return
        #~ if not self.model._meta.managed:
            #~ print "NOT MANAGED: ", self.model
            #~ return
        
        if self.model._meta.abstract:
            return
            
        self.detail_layouts = self.model._lino_detail
        assert type(self.detail_layouts) is list
            
        #~ for b in self.model.__bases__:
            #~ if issubclass(b,models.Model) and b is not models.Model:
                #~ for dtl in getattr(b,'_lino_detail_layouts',[]):
                    #~ self.detail_layouts.append(dtl)
        #~ for dtl in getattr(self.model,'_lino_detail_layouts',[]):
            #~ self.detail_layouts.append(dtl)
            
        #~ if self.detail_layouts:
            #~ print 20110822, self, [dl.filename for dl in self.detail_layouts]

        
            
        
    def get_data_elem(self,name): 
        cc = self.computed_columns.get(name,None)
        if cc:
            return cc
        return get_data_elem(self.model,name)
        #~ de = get_data_elem(self.model,name)
        #~ if de is not None: 
            #~ return de
        #~ return self.get_action(name)
        
        
    def get_detail(self):
        return self.model._lino_detail
        
    def get_title(self,rr):
        """
        Return the title of this Table for the given request `rr`.
        Override this if your Table's title should mention for example filter conditions.
        """
        assert rr is not None
        #~ if rr is not None and self.master is not None:
        if self.master is not None:
            #~ return _("%(details)s by %(model)s %(master)s") % dict(
            return _("%(details)s of %(master)s") % dict(
              #~ model=self.master._meta.verbose_name,
              #~ model=rr.master_instance._meta.verbose_name,
              details=self.model._meta.verbose_name_plural,
              master=rr.master_instance)
        return self.title or self.label
        
    def get_queryset(self):
        """
        Return an iterable over the items processed by this report.
        Override this to use e.g. select_related()
        or to return a list.
        """
        return self.model.objects.all()
      
    def get_request_queryset(self,rr):
        """
        Build a Queryset for the specified request on this report.
        Upon first call, this will also lazily install Table.queryset 
        which will be reused on every subsequent call.
        """
        if self.base_queryset is None:
            self.base_queryset = self.get_queryset()
        qs = self.base_queryset
        #~ kw = self.get_filter_kw(rr.master_instance,**rr.params)
        kw = self.get_filter_kw(rr.master_instance)
        if kw is None:
            return []
        if len(kw):
            qs = qs.filter(**kw)

        if rr.exclude:
            #~ qs = qs.exclude(**rr.exclude)
            qs = qs.exclude(rr.exclude)
            
        if self.filter:
            #~ qs = qs.filter(**self.filter)
            qs = qs.filter(self.filter)
            
        if rr.filter:
            #~ print rr.filter
            #~ qs = qs.filter(**rr.filter)
            qs = qs.filter(rr.filter)
            
        if rr.known_values:
            d = {}
            for k,v in rr.known_values.items():
                if v is None:
                    d[k+"__isnull"] = True
                else:
                    #~ d[k+"__exact"] = v
                    d[k] = v
                qs = qs.filter(**d)
                
        if self.exclude:
            qs = qs.exclude(**self.exclude)
              
        if rr.quick_search is not None:
            #~ qs = add_quick_search_filter(qs,self.model,rr.quick_search)
            qs = add_quick_search_filter(qs,rr.quick_search)
        if rr.gridfilters is not None:
            qs = add_gridfilters(qs,rr.gridfilters)
        extra = rr.extra or self.extra
        if extra is not None:
            qs = qs.extra(**extra)
        order_by = rr.order_by or self.order_by
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def slave_as_summary_meth(self,ui,row_separator):
        """
        Creates and returns the method to be used when :attr:`Table.show_slave_grid` is `False`.
        """
        def meth(master,request):
            rr = TableRequest(ui,self,None,self.default_action,master_instance=master)
            #~ rr = self.request(ui,master_instance=master)
            s = summary(ui,rr,row_separator)
            #~ s = ', '.join([fmt(r) for r in rr])
            #~ print 'reports.py 20101017', s
            return s
        return meth
        
        
    def setup_request(self,req):
        pass
        
        
    def get_create_kw(self,master_instance,**kw):
        return self.get_filter_kw(master_instance,**kw)
        
    def get_filter_kw(self,master_instance,**kw):
        #logger.debug('%s.get_filter_kw(%r) master=%r',self,kw,self.master)
        if self.master is None:
            assert master_instance is None, "Table %s doesn't accept a master" % self.actor_id
        elif self.master is models.Model:
            pass
        elif self.master is ContentType:
            #~ print 20110415
            if master_instance is None:
                pass
                #~ kw[self.fk.ct_field] = None
                #~ kw[self.fk.fk_field] = None
            else:
                ct = ContentType.objects.get_for_model(master_instance.__class__)
                kw[self.fk.ct_field] = ct
                kw[self.fk.fk_field] = master_instance.pk
        elif self.master_key is not None:
            if master_instance is None:
                if not self.fk.null:
                    return # cannot add rows to this report
            elif not isinstance(master_instance,self.master):
                raise Exception("%r is not a %s" % (master_instance,self.master.__name__))
            kw[self.fk.name] = master_instance
            
        #~ else:
            #~ kw['master'] = master_instance
        return kw
        
    #~ def on_create(self,instance,request):
        #~ pass
        
    def create_instance(self,req,**kw):
        instance = self.model(**kw)
        #~ self.on_create(instance,req)
        
        """
        Used e.g. by modlib.notes.Note.on_create().
        on_create gets the request as argument.
        Didn't yet find out how to do that using a standard Django signal.
        """
        m = getattr(instance,'on_create',None)
        if m:
            m(req)
        #~ print 20110128, instance
        return instance
        
    #~ def get_label(self):
        #~ return self.label
        
    #~ def __str__(self):
        #~ return rc_name(self.__class__)
        
    def ajax_update(self,request):
        print request.POST
        return HttpResponse("1", mimetype='text/x-json')


    #~ @classmethod
    #~ def reset_details(cls):
        #~ return
        #~ cls.detail_layouts = []
      
    #~ @classmethod
    #~ def add_detail(cls,*args,**kw):
        #~ return
        #~ dtl = DetailLayout(*args,**kw)
        #~ cls.detail_layouts = list(cls.detail_layouts) # disconnect from base class
        #~ for i,layout in enumerate(cls.detail_layouts):
            #~ if layout.label == dtl.label:
                #~ cls.detail_layouts[i] = dtl
                #~ return
        #~ cls.detail_layouts.append(dtl)
        
    @classmethod
    def request(cls,ui=None,request=None,**kw):
        self = cls()
        return TableRequest(ui,self,request,self.default_action,**kw)
        #~ return self.default_action.request(ui,**kw)
        

    def row2dict(self,row,d):
        """
        Overridden by lino.modlib.properties.PropValuesByOwner.
        See also lino.ui.extjs.ext_requests.ViewReportRequest.
        """
        for n in self.column_names.split():
            d[n] = getattr(row,n)
        return d
        
    def save_grid_config(self,index,data):
        if len(self.grid_configs) == 0:
            gc = GridConfig(self,data,'%s.gc' % self)
            self.grid_configs.append(gc)
        else:
            gc = self.grid_configs[index]
        gc.data = data
        gc.validate()
        #~ self.grid_configs[index] = gc
        return gc.save_config()
        #~ filename = self.get_grid_config_file(gc)
        #~ f = open(filename,'w')
        #~ f.write("# Generated file. Delete it to restore default configuration.\n")
        #~ d = dict(grid_configs=self.grid_configs)
        #~ f.write(yaml.dump(d))
        #~ f.close()
        #~ return "Grid Config has been saved to %s" % filename
        
def report_factory(model):
    #~ logger.info('report_factory(%s)',model.__name__)
    bases = (Table,)
    for b in model.__bases__:
        rpt = getattr(b,'_lino_model_report',None)
        if rpt is not None:
            if issubclass(model,rpt.model):
            #~ if issubclass(rpt.model,model):
                bases = (rpt.__class__,)
    #~ logger.info('report_factory(%s) : bases is %s',model.__name__,bases)
    cls = type(model.__name__+"Table",
        bases,dict(model=model,
            app_label=model._meta.app_label))
    return actors.register_actor(cls())


def column_choices(rptname):
    rpt = actors.get_actor(rptname)
    return rpt.column_choices()


class LayoutError(RuntimeError):
    pass
  
LABEL_ALIGN_TOP = 'top'
LABEL_ALIGN_LEFT = 'left'
LABEL_ALIGN_RIGHT = 'right'


class GridConfig(Configured):
  
    def __init__(self,report,data,*args,**kw):
        self.report = report
        self.data = data
        self.label_en = data.get('label')
        self.data.update(label=_(self.label_en))
        super(GridConfig,self).__init__(*args,**kw)
        must_save = self.validate()
        if must_save:
            msg = self.save_config()
            #~ msg = self.save_grid_config()
            logger.debug(msg)
  
    def validate(self):
        """
        Removes unknown columns
        """
        must_save = False
        gc = self.data
        columns = gc['columns']
        col_count = len(columns)
        widths = gc.get('widths',None)
        hiddens = gc.get('hiddens',None)
        if widths is None:
            widths = [None for x in columns]
            gc.update(widths=widths)
        elif col_count != len(widths):
            raise Exception("%d columns, but %d widths" % (col_count,len(widths)))
        if hiddens is None:
            hiddens = [False for x in columns]
            gc.update(hiddens=hiddens)
        elif col_count != len(hiddens):
            raise Exception("%d columns, but %d hiddens" % (col_count,len(hiddens)))
            
        valid_columns = []
        valid_widths = []
        valid_hiddens = []
        for i,colname in enumerate(gc['columns']):
            f = self.report.get_data_elem(colname)
            if f is None:
                logger.debug("Removed unknown column %d (%r). Must save.",i,colname)
                must_save = True
            else:
                valid_columns.append(colname)
                valid_widths.append(widths[i])
                valid_hiddens.append(hiddens[i])
        gc.update(widths=valid_widths)
        gc.update(hiddens=valid_hiddens)
        gc.update(columns=valid_columns)
        return must_save
            
    def unused_write_content(self,f):
        self.data.update(label=self.label_en)
        f.write(yaml.dump(self.data))
        self.data.update(label=_(self.label_en))
        
    def write_content(self,f):
        f.write(yaml.dump(self.data))
        
        
        
class BaseLayout(Configured):
    label = None
    has_frame = False # True
    label_align = LABEL_ALIGN_TOP
    hideCheckBoxLabels = True
    #label_align = LABEL_ALIGN_LEFT
    default_button = None
    collapsible_elements  = {}
    write_debug_info = False
    
    def __init__(self,desc,*args,**kw):
        #~ self.label = label
        self._desc = desc
        #~ super(BaseLayout,self).__init__(*args,**kw)
        Configured.__init__(self,*args,**kw)
            
        attrname = None
        for ln in desc.splitlines():
            if ln and not ln.lstrip().startswith('## '):
                if ln[0].isspace():
                    if attrname is None:
                        raise LayoutError('Unexpected indentation.')
                    v = getattr(self,attrname) + '\n' + ln.strip()
                    setattr(self,attrname,v) 
                elif ln.startswith(':'):
                    a = ln.split(':',2)
                    if len(a) != 3:
                        raise LayoutError('Expected attribute `:attr:value` ')
                    attname = a[1]
                    if not hasattr(self,attname):
                        raise LayoutError('Invalid layout field %r' % attname)
                    setattr(self,attname,a[2].strip())
                else:
                    a = ln.split('=',1)
                    if len(a) != 2:
                        raise LayoutError('"=" expected in %r' % ln)
                    attrname = a[0].strip()
                    if hasattr(self,attrname):
                        raise Exception(
                            'Duplicate element definition %r in %r' 
                            % (attrname,desc))
                    setattr(self,attrname,a[1].strip())
        if self.label:
            #~ settings.LINO.add_dummy_message(self.label)
            self.add_dummy_message(self.label)
            self.label = _(self.label)
            
    #~ def __str__(self):
            
    def __str__(self):
        if self.filename:
            return "%s(%s %s)" % (self.__class__.__name__,self.cd.name,self.filename)
        return self.__class__.__name__ + "(" + self._desc + ")"
        #~ return "Dynamic " + super(Configured,self).__str__()
        
    def write_content(self,f):
        f.write(self._desc)
            
class ListLayout(BaseLayout):
    #~ label = _("List")
    show_labels = False
    join_str = " "
    
    #~ def setup_element(self,e):
        #~ if isinstance(e,TextFieldElement):
            #~ e.hidden = True

class DetailLayout(BaseLayout):
    #~ label = _("Detail")
    show_labels = True
    join_str = "\n"
    only_for_report = None



class LayoutHandle:
    """
    LayoutHandle analyzes a Layout and builds a tree of LayoutElements.
    
    """
    start_focus = None
    
    #~ def __init__(self,rh,layout,hidden_elements=frozenset()):
    def __init__(self,ui,model,layout,hidden_elements=frozenset()):
      
        #~ logger.debug('20111113 %s.__init__(%s,%s)',self.__class__.__name__,rh,layout)
        assert isinstance(layout,BaseLayout)
        #assert isinstance(link,reports.ReportHandle)
        #~ base.Handle.__init__(self,ui)
        #~ actors.ActorHandle.__init__(self,layout)
        self.layout = layout
        self.ui = ui
        self.model = model
        #~ self.rh = rh
        #~ self.datalink = layout.get_datalink(ui)
        #~ self.name = layout._actor_name
        self.label = layout.label # or ''
        self._store_fields = []
        #~ self._elems_by_field = {}
        #~ self._submit_fields = []
        #~ self.slave_grids = []
        #~ self._buttons = []
        self.hidden_elements = hidden_elements # layout.get_hidden_elements(self)
        self.main_class = ui.main_panel_class(layout)
        
        #~ if layout.main is not None:
        if layout.main:
        #~ if hasattr(layout,"main"):
            self._main = self.create_element(self.main_class,'main')
            if self._main is None:
                raise Exception("%s.%s could not create main element" 
                    % (model,self.layout))
        else:
            raise Exception("%s has no main" % self.layout)
            
        #~ if isinstance(self.layout,ListLayout):
            #~ assert len(self._main.elements) > 0, "%s : Grid has no columns" % self
            #~ self.columns = self._main.elements
            
        #~ self.width = self.layout.width or self._main.width
        #~ self.height = self.layout.height or self._main.height
        self.width = self._main.width
        self.height = self._main.height
        if True:
            self.write_debug_info()
        
        #~ self.default_button = None
        #~ if layout.default_button is not None:
            #~ for e in self._buttons:
                #~ if e.name == layout.default_button:
                    #~ self.default_button = e
                    #~ break
                
    #~ def needs_store(self,rh):
        #~ self._needed_stores.add(rh)
        
    #~ def __str__(self):
        #~ return str(self.layout) + "Handle"
        
    def get_data_elem(self,name): return get_data_elem(self.model,name)
      
    def __str__(self):
        #~ return "%s %s" % (self.rh,self.__class__.__name__)
        return "%s %s" % (self.model,self.__class__.__name__)
        
    #~ def elems_by_field(self,name):
        #~ return self._elems_by_field.get(name,[])
        
    def add_store_field(self,field):
        self._store_fields.append(field)
            
    def has_field(self,f):
        return self._main.has_field(f)
        
    def unused__repr__(self):
        s = self.name # self.__class__.__name__ 
        if hasattr(self,'_main'):
            s += "(%s)" % self._main
        return s
        
    #~ def setup_element(self,e):
        #~ if e.name in self.hidden_elements:
            #~ e.hidden = True
            
    #~ def get_absolute_url(self,**kw):
        #~ return self.datalink.get_absolute_url(layout=self.index,**kw)
        
    def add_hidden_field(self,field):
        return HiddenField(self,field)
        
    def write_debug_info(self):
        if self.layout.filename and self.layout.write_debug_info:
            filename = "%s.debug.html" % self.layout.filename
            filename = os.path.join(self.layout.cd.name,filename)
            logger.info("Writing %s..." % filename)
            f = codecs.open(filename,"w",encoding='utf-8')
            f.write('''<html><body><table border="1">''')
            f.write('''<h1>%s</h1>''' % self)
            f.write(u"\n".join(self._main.debug_lines()))
            f.write('''</table></body></html>''')
            f.close()
        
    def get_title(self,ar):
        return self.layout.get_title(ar)
        
    def walk(self):
        return self._main.walk()
        
    def ext_lines(self,request):
        return self._main.ext_lines(request)
  
    def use_as_wildcard(self,de):
        if de.name.endswith('_ptr'): return False
        #~ and (de.name not in self.hidden_elements) \
        #~ and (de.name not in self.rh.report.known_values.keys()) \
        #~ if de.name == self.rh.report.master_key: return False
        return True
  
    def desc2elem(self,panelclass,desc_name,desc,**kw):
        #logger.debug("desc2elem(panelclass,%r,%r)",desc_name,desc)
        #assert desc != 'Countries_choices2'
        if '*' in desc:
            explicit_specs = set()
            for spec in desc.split():
                if spec != '*':
                    name,kw = self.splitdesc(spec)
                    explicit_specs.add(name)
            wildcard_fields = self.layout.join_str.join([
                de.name for de in wildcard_data_elems(self.model) \
                  
                  if (de.name not in explicit_specs) \
                    and self.use_as_wildcard(de) \
                ])
            desc = desc.replace('*',wildcard_fields)
            #~ if 'CourseRequestsByPerson' in str(self):
                #~ logger.info('20111003 %s desc -> %r',self,desc)
        if "\n" in desc:
            # it's a vertical box
            elems = []
            i = 0
            for x in desc.splitlines():
                x = x.strip()
                if len(x) > 0 and not x.startswith("# "):
                    i += 1
                    e = self.desc2elem(self.ui.Panel,desc_name+'_'+str(i),x,**kw)
                    if e is not None:
                        elems.append(e)
            if len(elems) == 0:
                return None
            if len(elems) == 1 and panelclass != self.main_class:
                return elems[0]
            #return self.vbox_class(self,name,*elems,**kw)
            return panelclass(self,desc_name,True,*elems,**kw)
        else:
            # it's a horizontal box
            elems = []
            for x in desc.split():
                if not x.startswith("#"):
                    """
                    20100214 dsbe.PersonDetail hatte 2 MainPanels, 
                    weil PageLayout kein einzeiliges (horizontales) `main` vertrug
                    """
                    e = self.create_element(self.ui.Panel,x)
                    if e is None:
                        pass
                    elif isinstance(e,list):
                        elems += e
                    else:
                        elems.append(e)
            if len(elems) == 0:
                return None
            if len(elems) == 1 and panelclass != self.main_class:
                return elems[0]
            #return self.hbox_class(self,name,*elems,**kw)
            return panelclass(self,desc_name,False,*elems,**kw)
            
    def create_element(self,panelclass,desc_name):
        #~ logger.debug("create_element(panelclass,%r)", desc_name)
        name,kw = self.splitdesc(desc_name)
        e = self.ui.create_layout_element(self,panelclass,name,**kw)
        # todo: cannot hide babelfields
        if name in self.hidden_elements:
            e.hidden = True
        #~ self.setup_element(e)
        return e
        
    def splitdesc(self,picture):
        a = picture.split(":",1)
        if len(a) == 1:
            return picture,{}
        if len(a) == 2:
            name = a[0]
            a = a[1].split("x",1)
            if len(a) == 1:
                return name, dict(width=int(a[0]))
            elif len(a) == 2:
                return name, dict(width=int(a[0]),height=int(a[1]))
        raise Exception("Invalid picture descriptor %s" % picture)
        
class ListLayoutHandle(LayoutHandle):
  
    def __init__(self,rh,*args,**kw):
        self.rh = rh
        LayoutHandle.__init__(self,rh.ui,rh.report.model,*args,**kw)
        
    def use_as_wildcard(self,de):
        if de.name.endswith('_ptr'): return False
        #~ and (de.name not in self.hidden_elements) \
        #~ and (de.name not in self.rh.report.known_values.keys()) \
        if de.name == self.rh.report.master_key: return False
        return True
  

class DetailHandle(base.Handle):
    """
    """
    def __init__(self,ui,detail):
        self.detail = detail
        #~ self.content_type = ContentType.objects.get_for_model(detail.model).pk
        self.lh_list = [ 
            LayoutHandle(ui,detail.model,dl) 
                for dl in self.detail.layouts ]
        base.Handle.__init__(self,ui)
      

class Detail(base.Handled):
    """
    The UI-agnostic representation of a Detail window.
    Equivalent to a collection of .dtl files.
    """
    
    _handle_class = DetailHandle
    
    def __init__(self,model,layouts):
        self.model = model
        self.layouts = layouts
        base.Handled.__init__(self)
        
