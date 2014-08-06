"""
:mod:`psphere.client` - A client for communicating with a vSphere server
========================================================================

.. module:: client

The main module for accessing a vSphere server.

.. moduleauthor:: Jonathan Kinred <jonathan.kinred@gmail.com>

"""

# Copyright 2010 Jonathan Kinred
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at:
# 
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import logging
import os
import suds
import time

from urllib2 import URLError
from suds.plugin import MessagePlugin
from suds.transport import TransportError

from psphere import soap, ManagedObject
from psphere.config import _config_value
from psphere.errors import (ConfigError, ObjectNotFoundError, TaskFailedError,
                            NotLoggedInError)
from psphere.managedobjects import ServiceInstance, Task, classmapper

logger = logging.getLogger(__name__)

class Client(suds.client.Client):
    """A client for communicating with a VirtualCenter/ESX/ESXi server

    >>> from psphere.client import Client
    >>> Client = Client(server="esx.foo.com", username="me", password="pass")

    :param server: The server of the server. e.g. https://esx.foo.com/sdk
    :type server: str
    :param username: The username to connect with
    :type username: str
    :param password: The password to connect with
    :type password: str
    :param wsdl_location: Whether to use the provided WSDL or load the server WSDL
    :type wsdl_location: The string "local" (default) or "remote"
    :param timeout: The timeout to use when connecting to the server
    :type timeout: int (default=30)
    :param plugins: The plugins classes that will be used to process messages
                    before send them to the web service
    :type plugins: list of classes
    """
    def __init__(self, server=None, username=None, password=None,
                 wsdl_location="local", timeout=30, plugins=[]):
        self._logged_in = False
        if server is None:
            server = _config_value("general", "server")
        if username is None:
            username = _config_value("general", "username")
        if password is None:
            password = _config_value("general", "password")
        if server is None:
            raise ConfigError("server must be set in config file or Client()")
        if username is None:
            raise ConfigError("username must be set in config file or Client()")
        if password is None:
            raise ConfigError("password must be set in config file or Client()")
        self.server = server
        self.username = username
        self.password = password
        url = "https://%s/sdk" % self.server
        if wsdl_location == "local":
            current_path = os.path.abspath(os.path.dirname(__file__))            
            current_path = current_path.replace('\\', '/')
            if not current_path.startswith('/') :
                current_path = '/' + current_path
            if current_path.endswith('/') :
                current_path = current_path[:-1]
            wsdl_uri = ("file://%s/wsdl/vimService.wsdl" % current_path)
        elif wsdl_location == "remote":
            wsdl_uri = url + "/vimService.wsdl"
        else:
            raise ValueError("wsdl_location must be \"local\" or \"remote\"")
        # Init the base class
        try:
            # Add ExtraConfigPlugin to the plugins
            plugins.append(ExtraConfigPlugin())
            suds.client.Client.__init__(self, wsdl_uri, plugins=plugins)
        except URLError:
            logger.critical("Failed to connect to %s", self.server)
            raise
        except IOError:
            logger.critical("Failed to load the local WSDL from %s", wsdl_uri)
            raise
        except TransportError:
            logger.critical("Failed to load the remote WSDL from %s", wsdl_uri)
            raise
        self.options.transport.options.timeout = timeout
        self.set_options(location=url)
        mo_ref = soap.ManagedObjectReference("ServiceInstance",
                                             "ServiceInstance")
        self.si = ServiceInstance(mo_ref, self) 
        try:
            self.sc = self.si.RetrieveServiceContent()
        except URLError, e:
            logger.critical("Failed to connect to %s" % self.server)
            logger.critical("urllib2 said: %s" % e.reason) 
            raise

        if self._logged_in is False:
            self.login(self.username, self.password)

    def login(self, username=None, password=None):
        """Login to a vSphere server.

        >>> client.login(username='Administrator', password='strongpass')

        :param username: The username to authenticate as.
        :type username: str
        :param password: The password to authenticate with.
        :type password: str
        """
        if username is None:
            username = self.username
        if password is None:
            password = self.password
        logger.debug("Logging into server")
        self.sc.sessionManager.Login(userName=username, password=password)
        self._logged_in = True

    def logout(self):
        """Logout of a vSphere server."""
        if self._logged_in is True:
            self.si.flush_cache()
            self.sc.sessionManager.Logout()
            self._logged_in = False

    def invoke(self, method, _this, **kwargs):
        """Invoke a method on the server.

        >>> client.invoke('CurrentTime', client.si)

        :param method: The method to invoke, as found in the SDK.
        :type method: str
        :param _this: The managed object reference against which to invoke \
        the method.
        :type _this: ManagedObject
        :param kwargs: The arguments to pass to the method, as \
        found in the SDK.
        :type kwargs: TODO

        """
        if (self._logged_in is False and
            method not in ["Login", "RetrieveServiceContent"]):
            logger.critical("Cannot exec %s unless logged in", method)
            raise NotLoggedInError("Cannot exec %s unless logged in" % method)

        for kwarg in kwargs:
            kwargs[kwarg] = self._marshal(kwargs[kwarg])

        result = getattr(self.service, method)(_this=_this, **kwargs)
        if hasattr(result, '__iter__') is False:
            logger.debug("Returning non-iterable result")
            return result

        # We must traverse the result and convert any ManagedObjectReference
        # to a psphere class, this will then be lazy initialised on use
        logger.debug(result.__class__)
        logger.debug("Result: %s", result)
        logger.debug("Length: %s", len(result))
        if type(result) == list:
            new_result = []
            for item in result:
                new_result.append(self._unmarshal(item))
        else:
            new_result = self._unmarshal(result)
            
        logger.debug("Finished in invoke.")
        #property = self.find_and_destroy(property)
        #print result
        # Return the modified result to the caller
        return new_result

    def _mor_to_pobject(self, mo_ref):
        """Converts a MOR to a psphere object."""
        kls = classmapper(mo_ref._type)
        new_object = kls(mo_ref, self)
        return new_object

    def _marshal(self, obj):
        """Walks an object and marshals any psphere object into MORs."""
        logger.debug("Checking if %s needs to be marshalled", obj)
        if isinstance(obj, ManagedObject):
            logger.debug("obj is a psphere object, converting to MOR")
            return obj._mo_ref

        if isinstance(obj, list):
            logger.debug("obj is a list, recursing it")
            new_list = []
            for item in obj:
                new_list.append(self._marshal(item))
            return new_list
                
        if not isinstance(obj, suds.sudsobject.Object):
            logger.debug("%s is not a sudsobject subclass, skipping", obj)
            return obj

        if hasattr(obj, '__iter__'):
            logger.debug("obj is iterable, recursing it")
            for (name, value) in obj:
                setattr(obj, name, self._marshal(value))
            return obj
            
        # The obj has nothing that we want to marshal or traverse, return it
        logger.debug("obj doesn't need to be marshalled")
        return obj

    def _unmarshal(self, obj):
        """Walks an object and unmarshals any MORs into psphere objects."""
        if isinstance(obj, suds.sudsobject.Object) is False:
            logger.debug("%s is not a suds instance, skipping", obj)
            return obj

        logger.debug("Processing:")
        logger.debug(obj)
        logger.debug("...with keylist:")
        logger.debug(obj.__keylist__)
        # If the obj that we're looking at has a _type key
        # then create a class of that type and return it immediately
        if "_type" in obj.__keylist__:
            logger.debug("obj is a MOR, converting to psphere class")
            return self._mor_to_pobject(obj)

        new_object = obj.__class__()
        for sub_obj in obj:
            logger.debug("Looking at %s of type %s", sub_obj, type(sub_obj))

            if isinstance(sub_obj[1], list):
                new_embedded_objs = []
                for emb_obj in sub_obj[1]:
                    new_emb_obj = self._unmarshal(emb_obj)
                    new_embedded_objs.append(new_emb_obj)
                setattr(new_object, sub_obj[0], new_embedded_objs)
                continue

            if not issubclass(sub_obj[1].__class__, suds.sudsobject.Object):
                logger.debug("%s is not a sudsobject subclass, skipping",
                             sub_obj[1].__class__)
                setattr(new_object, sub_obj[0], sub_obj[1])
                continue

            logger.debug("Obj keylist: %s", sub_obj[1].__keylist__)
            if "_type" in sub_obj[1].__keylist__:
                logger.debug("Converting nested MOR to psphere class:")
                logger.debug(sub_obj[1])
                kls = classmapper(sub_obj[1]._type)
                logger.debug("Setting %s.%s to %s",
                             new_object.__class__.__name__,
                             sub_obj[0],
                             sub_obj[1])
                setattr(new_object, sub_obj[0], kls(sub_obj[1], self))
            else:
                logger.debug("Didn't find _type in:")
                logger.debug(sub_obj[1])
                setattr(new_object, sub_obj[0], self._unmarshal(sub_obj[1]))

        return new_object

    def create(self, type_, **kwargs):
        """Create a SOAP object of the requested type.

        >>> client.create('VirtualE1000')

        :param type_: The type of SOAP object to create.
        :type type_: str
        :param kwargs: TODO
        :type kwargs: TODO

        """
        obj = self.factory.create("ns0:%s" % type_)
        for key, value in kwargs.items():
            setattr(obj, key, value)
        return obj

#        Notes
#        -----
#        A view is a local, static representation of a managed object in
#        the inventory. The view is not automatically synchronised with 
#        the server-side object and can therefore be out of date a moment
#        after it is retrieved.
#        
#        Retrieval of only the properties you intend to use -- through
#        the use of the properties parameter -- is considered best
#        practise as the properties of some managed objects can be
#        costly to retrieve.

    def get_view(self, mo_ref, properties=None):
        """Get a view of a vSphere managed object.
        
        :param mo_ref: The MOR to get a view of
        :type mo_ref: ManagedObjectReference
        :param properties: A list of properties to retrieve from the \
        server
        :type properties: list
        :returns: A view representing the ManagedObjectReference.
        :rtype: ManagedObject

        """
        # This maps the mo_ref into a psphere class and then instantiates it
        kls = classmapper(mo_ref._type)
        view = kls(mo_ref, self)
        # Update the requested properties of the instance
        #view.update_view_data(properties=properties)

        return view

    def get_views(self, mo_refs, properties=None):
        """Get a list of local view's for multiple managed objects.

        :param mo_refs: The list of ManagedObjectReference's that views are \
        to be created for.
        :type mo_refs: ManagedObjectReference
        :param properties: The properties to retrieve in the views.
        :type properties: list
        :returns: A list of local instances representing the server-side \
        managed objects.
        :rtype: list of ManagedObject's

        """
        property_specs = []
        for mo_ref in mo_refs:
            property_spec = self.create('PropertySpec')
            property_spec.type = str(mo_ref._type)
            if properties is None:
                properties = []
            else:
                # Only retrieve the requested properties
                if properties == "all":
                    property_spec.all = True
                else:
                    property_spec.all = False
                    property_spec.pathSet = properties
            property_specs.append(property_spec)

        object_specs = []
        for mo_ref in mo_refs:
            object_spec = self.create('ObjectSpec')
            object_spec.obj = mo_ref
            object_specs.append(object_spec)

        pfs = self.create('PropertyFilterSpec')
        pfs.propSet = property_specs
        pfs.objectSet = object_specs

        object_contents = self.sc.propertyCollector.RetrieveProperties(
            specSet=pfs)
        views = []
        for object_content in object_contents:
            # Update the instance with the data in object_content
            object_content.obj._set_view_data(object_content=object_content)
            views.append(object_content.obj)

        return views
        
    def get_search_filter_spec(self, begin_entity, property_spec):
        """Build a PropertyFilterSpec capable of full inventory traversal.
        
        By specifying all valid traversal specs we are creating a PFS that
        can recursively select any object under the given entity.

        :param begin_entity: The place in the MOB to start the search.
        :type begin_entity: ManagedEntity
        :param property_spec: TODO
        :type property_spec: TODO
        :returns: A PropertyFilterSpec, suitable for recursively searching \
        under the given ManagedEntity.
        :rtype: PropertyFilterSpec

        """
        # The selection spec for additional objects we want to filter
        ss_strings = ['resource_pool_traversal_spec',
                      'resource_pool_vm_traversal_spec',
                      'folder_traversal_spec',
                      'datacenter_host_traversal_spec',
                      'datacenter_vm_traversal_spec',
                      'compute_resource_rp_traversal_spec',
                      'compute_resource_host_traversal_spec',
                      'host_vm_traversal_spec']

        # Create a selection spec for each of the strings specified above
        selection_specs = [
            self.create('SelectionSpec', name=ss_string)
            for ss_string in ss_strings
        ]

        # A traversal spec for deriving ResourcePool's from found VMs
        rpts = self.create('TraversalSpec')
        rpts.name = 'resource_pool_traversal_spec'
        rpts.type = 'ResourcePool'
        rpts.path = 'resourcePool'
        rpts.selectSet = [selection_specs[0], selection_specs[1]]

        # A traversal spec for deriving ResourcePool's from found VMs
        rpvts = self.create('TraversalSpec')
        rpvts.name = 'resource_pool_vm_traversal_spec'
        rpvts.type = 'ResourcePool'
        rpvts.path = 'vm'

        crrts = self.create('TraversalSpec')
        crrts.name = 'compute_resource_rp_traversal_spec'
        crrts.type = 'ComputeResource'
        crrts.path = 'resourcePool'
        crrts.selectSet = [selection_specs[0], selection_specs[1]]

        crhts = self.create('TraversalSpec')
        crhts.name = 'compute_resource_host_traversal_spec'
        crhts.type = 'ComputeResource'
        crhts.path = 'host'
         
        dhts = self.create('TraversalSpec')
        dhts.name = 'datacenter_host_traversal_spec'
        dhts.type = 'Datacenter'
        dhts.path = 'hostFolder'
        dhts.selectSet = [selection_specs[2]]

        dvts = self.create('TraversalSpec')
        dvts.name = 'datacenter_vm_traversal_spec'
        dvts.type = 'Datacenter'
        dvts.path = 'vmFolder'
        dvts.selectSet = [selection_specs[2]]

        hvts = self.create('TraversalSpec')
        hvts.name = 'host_vm_traversal_spec'
        hvts.type = 'HostSystem'
        hvts.path = 'vm'
        hvts.selectSet = [selection_specs[2]]
      
        fts = self.create('TraversalSpec')
        fts.name = 'folder_traversal_spec'
        fts.type = 'Folder'
        fts.path = 'childEntity'
        fts.selectSet = [selection_specs[2], selection_specs[3],
                          selection_specs[4], selection_specs[5],
                          selection_specs[6], selection_specs[7],
                          selection_specs[1]]

        obj_spec = self.create('ObjectSpec')
        obj_spec.obj = begin_entity
        obj_spec.selectSet = [fts, dvts, dhts, crhts, crrts,
                               rpts, hvts, rpvts]

        pfs = self.create('PropertyFilterSpec')
        pfs.propSet = [property_spec]
        pfs.objectSet = [obj_spec]
        return pfs

    def invoke_task(self, method, **kwargs):
        """Execute a \*_Task method and wait for it to complete.
        
        :param method: The \*_Task method to invoke.
        :type method: str
        :param kwargs: The arguments to pass to the method.
        :type kwargs: TODO

        """
        # Don't execute methods which don't return a Task object
        if not method.endswith('_Task'):
            logger.error('invoke_task can only be used for methods which '
                  'return a ManagedObjectReference to a Task.')
            return None

        task_mo_ref = self.invoke(method=method, **kwargs)
        task = Task(task_mo_ref, self)
        task.update_view_data(properties=['info'])
        # TODO: This returns true when there is an error
        while True:
            if task.info.state == 'success':
                return task
            elif task.info.state == 'error':
                # TODO: Handle error checking properly
                raise TaskFailedError(task.info.error.localizedMessage)

            # TODO: Implement progresscallbackfunc
            # Sleep two seconds and then refresh the data from the server
            time.sleep(2)
            task.update_view_data(properties=['info'])

    def find_entity_views(self, view_type, begin_entity=None, properties=None):
        """Find all ManagedEntity's of the requested type.

        :param view_type: The type of ManagedEntity's to find.
        :type view_type: str
        :param begin_entity: The MOR to start searching for the entity. \
        The default is to start the search at the root folder.
        :type begin_entity: ManagedObjectReference or None
        :returns: A list of ManagedEntity's
        :rtype: list

        """
        if properties is None:
            properties = []

        # Start the search at the root folder if no begin_entity was given
        if not begin_entity:
            begin_entity = self.sc.rootFolder._mo_ref

        property_spec = self.create('PropertySpec')
        property_spec.type = view_type
        property_spec.all = False
        property_spec.pathSet = properties

        pfs = self.get_search_filter_spec(begin_entity, property_spec)

        # Retrieve properties from server and update entity
        obj_contents = self.sc.propertyCollector.RetrieveProperties(specSet=pfs)

        views = []
        for obj_content in obj_contents:
            logger.debug("In find_entity_view with object of type %s",
                         obj_content.obj.__class__.__name__)
            obj_content.obj.update_view_data(properties=properties)
            views.append(obj_content.obj)

        return views

    def find_entity_view(self, view_type, begin_entity=None, filter={},
                         properties=None):
        """Find a ManagedEntity of the requested type.

        Traverses the MOB looking for an entity matching the filter.

        :param view_type: The type of ManagedEntity to find.
        :type view_type: str
        :param begin_entity: The MOR to start searching for the entity. \
        The default is to start the search at the root folder.
        :type begin_entity: ManagedObjectReference or None
        :param filter: Key/value pairs to filter the results. The key is \
        a valid parameter of the ManagedEntity type. The value is what \
        that parameter should match.
        :type filter: dict
        :returns: If an entity is found, a ManagedEntity matching the search.
        :rtype: ManagedEntity

        """
        if properties is None:
            properties = []

        kls = classmapper(view_type)
        # Start the search at the root folder if no begin_entity was given
        if not begin_entity:
            begin_entity = self.sc.rootFolder._mo_ref
            logger.debug("Using %s", self.sc.rootFolder._mo_ref)

        property_spec = self.create('PropertySpec')
        property_spec.type = view_type
        property_spec.all = False
        property_spec.pathSet = filter.keys()

        pfs = self.get_search_filter_spec(begin_entity, property_spec)

        # Retrieve properties from server and update entity
        #obj_contents = self.propertyCollector.RetrieveProperties(specSet=pfs)
        obj_contents = self.sc.propertyCollector.RetrieveProperties(specSet=pfs)

        # TODO: Implement filtering
        if not filter:
            logger.warning('No filter specified, returning first match.')
            # If no filter is specified we just return the first item
            # in the list of returned objects
            logger.debug("Creating class in find_entity_view (filter)")
            view = kls(obj_contents[0].obj, self)
            logger.debug("Completed creating class in find_entity_view (filter)")
            #view.update_view_data(properties)
            return view

        matched = False
        # Iterate through obj_contents retrieved
        for obj_content in obj_contents:
            # If there are is no propSet, skip this one
            if not obj_content.propSet:
                continue

            matches = 0
            # Iterate through each property in the set
            for prop in obj_content.propSet:
                for key in filter.keys():
                    # If the property name is in the defined filter
                    if prop.name == key:
                        # ...and it matches the value specified
                        # TODO: Regex this?
                        if prop.val == filter[prop.name]:
                            # We've found a match
                            matches += 1
                        else:
                            break
                    else:
                        continue
            if matches == len(filter):
                filtered_obj_content = obj_content
                matched = True
                break
            else:
                continue

        if matched is not True:
            # There were no matches
            raise ObjectNotFoundError("No matching objects for filter")

        logger.debug("Creating class in find_entity_view")
        view = kls(filtered_obj_content.obj._mo_ref, self)
        logger.debug("Completed creating class in find_entity_view")
        #view.update_view_data(properties=properties)
        return view

class ExtraConfigPlugin(MessagePlugin):
    def addAttributeForValue(self, node):
        if node.parent.name == 'extraConfig' and node.name == 'value':
            node.set('xsi:type', 'xsd:string')
    def marshalled(self, context):
        context.envelope.walk(self.addAttributeForValue)
