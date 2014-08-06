#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c)2012 Rackspace US, Inc.

# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from functools import wraps

import six

from pyrax.client import BaseClient
import pyrax.exceptions as exc
from pyrax.manager import BaseManager
from pyrax.resource import BaseResource
import pyrax.utils as utils


def assure_instance(fnc):
    @wraps(fnc)
    def _wrapped(self, instance, *args, **kwargs):
        if not isinstance(instance, CloudDatabaseInstance):
            # Must be the ID
            instance = self._manager.get(instance)
        return fnc(self, instance, *args, **kwargs)
    return _wrapped



class CloudDatabaseVolume(object):
    instance = None
    size = None
    used = None

    def __init__(self, instance, info):
        self.instance = instance
        for key, val in info.items():
            setattr(self, key, val)


    def resize(self, size):
        """
        Resize the volume to the specified size (in GB).
        """
        self.instance.resize_volume(size)
        self.size = size


    def get(self, att):
        """
        For compatibility with regular resource objects.
        """
        return getattr(self, att)



class CloudDatabaseManager(BaseManager):
    """
    This class manages communication with Cloud Database instances.
    """
    def get(self, item):
        """
        This additional code is necessary to properly return the 'volume'
        attribute of the instance as a CloudDatabaseVolume object instead of
        a raw dict.
        """
        resource = super(CloudDatabaseManager, self).get(item)
        resource.volume = CloudDatabaseVolume(resource, resource.volume)
        return resource


    def _create_body(self, name, flavor=None, volume=None, databases=None,
            users=None):
        """
        Used to create the dict required to create a Cloud Database instance.
        """
        if flavor is None:
            flavor = 1
        flavor_ref = self.api._get_flavor_ref(flavor)
        if volume is None:
            volume = 1
        if databases is None:
            databases = []
        if users is None:
            users = []
        body = {"instance": {
                "name": name,
                "flavorRef": flavor_ref,
                "volume": {"size": volume},
                "databases": databases,
                "users": users,
                }}
        return body


    def create_backup(self, instance, name, description=None):
        """
        Creates a backup of the specified instance, giving it the specified
        name along with an optional description.
        """
        body = {"backup": {
                "instance": utils.get_id(instance),
                "name": name,
                }}
        if description is not None:
            body["backup"]["description"] = description
        uri = "/backups"
        resp, resp_body = self.api.method_post(uri, body=body)
        mgr = self.api._backup_manager
        return CloudDatabaseBackup(mgr, body.get("backup"))


    def restore_backup(self, backup, name, flavor, volume):
        """
        Restores a backup to a new database instance. You must supply a backup
        (either the ID or a CloudDatabaseBackup object), a name for the new
        instance, as well as a flavor and volume size (in GB) for the instance.
        """
        flavor_ref = self.api._get_flavor_ref(flavor)
        body = {"instance": {
                "name": name,
                "flavorRef": flavor_ref,
                "volume": {"size": volume},
                "restorePoint": {"backupRef": utils.get_id(backup)},
                }}
        uri = "/%s" % self.uri_base
        resp, resp_body = self.api.method_post(uri, body=body)
        return CloudDatabaseInstance(self, resp_body.get("instance", {}))


    def list_backups(self, instance=None):
        """
        Returns a list of all backups by default, or just for a particular
        instance.
        """
        return self.api._backup_manager.list(instance=instance)


    def _list_backups_for_instance(self, instance):
        """
        Instance-specific backups are handled through the instance manager,
        not the backup manager.
        """
        uri = "/%s/%s/backups" % (self.uri_base, utils.get_id(instance))
        resp, resp_body = self.api.method_get(uri)
        mgr = self.api._backup_manager
        return [CloudDatabaseBackup(mgr, backup)
                for backup in resp_body.get("backups")]



class CloudDatabaseDatabaseManager(BaseManager):
    """
    This class manages communication with databases on Cloud Database instances.
    """
    def _create_body(self, name, character_set=None, collate=None):
        body = {"databases": [
                {"name": name,
                "character_set": character_set,
                "collate": collate,
                }]}
        return body



class CloudDatabaseUserManager(BaseManager):
    """
    This class handles operations on the users in a database on a Cloud
    Database instance.
    """
    def _create_body(self, name, password, databases=None, database_names=None,
            host=None):
        db_dicts = [{"name": db} for db in database_names]
        body = {"users": [
                {"name": name,
                "password": password,
                "databases": db_dicts,
                }]}
        if host:
            body["users"][0]["host"] = host
        return body


    def _get_db_names(self, dbs, strict=True):
        """
        Accepts a single db (name or object) or a list of dbs, and returns a
        list of database names. If any of the supplied dbs do not exist, a
        NoSuchDatabase exception will be raised, unless you pass strict=False.
        """
        dbs = utils.coerce_string_to_list(dbs)
        db_names = [utils.get_name(db) for db in dbs]
        if strict:
            good_dbs = self.instance.list_databases()
            good_names = [utils.get_name(good_db) for good_db in good_dbs]
            bad_names = [db_name for db_name in db_names
                    if db_name not in good_names]
            if bad_names:
                bad = ", ".join(bad_names)
                raise exc.NoSuchDatabase("The following database(s) were not "
                        "found: %s" % bad)
        return db_names


    def change_user_password(self, user, new_pass):
        """
        Changes the password for the user to the supplied value.

        Returns None upon success; raises PasswordChangeFailed if the call
        does not complete successfully.
        """
        return self.update(user, password=new_pass)


    def update(self, user, name=None, password=None, host=None):
        """
        Allows you to change one or more of the user's username, password, or
        host.
        """
        if not any((name, password, host)):
            raise exc.MissingDBUserParameters("You must supply at least one of "
                    "the following: new username, new password, or new host "
                    "specification.")
        if not isinstance(user, CloudDatabaseUser):
            # Must be the ID/name
            user = self.get(user)
        dct = {}
        if name and (name != user.name):
            dct["name"] = name
        if host and (host != user.host):
            dct["host"] = host
        if password:
            dct["password"] = password
        if not dct:
            raise exc.DBUpdateUnchanged("You must supply at least one changed "
                    "value when updating a user.")
        uri = "/%s/%s" % (self.uri_base, user.name)
        body = {"user": dct}
        resp, resp_body = self.api.method_put(uri, body=body)
        return None


    def list_user_access(self, user):
        """
        Returns a list of all database names for which the specified user
        has access rights.
        """
        user = utils.get_name(user)
        uri = "/%s/%s/databases" % (self.uri_base, user)
        try:
            resp, resp_body = self.api.method_get(uri)
        except exc.NotFound as e:
            raise exc.NoSuchDatabaseUser("User '%s' does not exist." % user)
        dbs = resp_body.get("databases", {})
        return [CloudDatabaseDatabase(self, db) for db in dbs]


    def grant_user_access(self, user, db_names, strict=True):
        """
        Gives access to the databases listed in `db_names` to the user. You may
        pass in either a single db or a list of dbs.

        If any of the databases do not exist, a NoSuchDatabase exception will
        be raised, unless you specify `strict=False` in the call.
        """
        user = utils.get_name(user)
        uri = "/%s/%s/databases" % (self.uri_base, user)
        db_names = self._get_db_names(db_names, strict=strict)
        dbs = [{"name": db_name} for db_name in db_names]
        body = {"databases": dbs}
        try:
            resp, resp_body = self.api.method_put(uri, body=body)
        except exc.NotFound as e:
            raise exc.NoSuchDatabaseUser("User '%s' does not exist." % user)


    def revoke_user_access(self, user, db_names, strict=True):
        """
        Revokes access to the databases listed in `db_names` for the user.

        If any of the databases do not exist, a NoSuchDatabase exception will
        be raised, unless you specify `strict=False` in the call.
        """
        user = utils.get_name(user)
        db_names = self._get_db_names(db_names, strict=strict)
        bad_names = []
        for db_name in db_names:
            uri = "/%s/%s/databases/%s" % (self.uri_base, user, db_name)
            resp, resp_body = self.api.method_delete(uri)



class CloudDatabaseBackupManager(BaseManager):
    """
    This class handles operations on backups for a Cloud Database instance.
    """
    def _create_body(self, name, instance, description=None):
        body = {"backup": {
                "instance": utils.get_id(instance),
                "name": name,
                }}
        if description is not None:
            body["backup"]["description"] = description
        return body


    def list(self, instance=None):
        """
        Return a list of all backups by default, or just for a particular
        instance.
        """
        if instance is None:
            return super(CloudDatabaseBackupManager, self).list()
        return self.api._manager._list_backups_for_instance(instance)



class CloudDatabaseInstance(BaseResource):
    """
    This class represents a MySQL instance in the cloud.
    """
    def __init__(self, *args, **kwargs):
        super(CloudDatabaseInstance, self).__init__(*args, **kwargs)
        self._database_manager = CloudDatabaseDatabaseManager(self.manager.api,
                resource_class=CloudDatabaseDatabase, response_key="database",
                uri_base="instances/%s/databases" % self.id)
        self._user_manager = CloudDatabaseUserManager(self.manager.api,
                resource_class=CloudDatabaseUser, response_key="user",
                uri_base="instances/%s/users" % self.id)
        # Add references to the parent instance to the managers.
        self._database_manager.instance = self._user_manager.instance = self
        # Remove the lazy load
        if not self.loaded:
            self.get()


    def get(self):
        """
        Need to override the default get() behavior by making the 'volume'
        attribute into a CloudDatabaseVolume object instead of the raw dict.
        """
        super(CloudDatabaseInstance, self).get()
        # Make the volume into an accessible object instead of a dict
        self.volume = CloudDatabaseVolume(self, self.volume)


    def list_databases(self, limit=None, marker=None):
        """Returns a list of the names of all databases for this instance."""
        return self._database_manager.list(limit=limit, marker=marker)


    def list_users(self, limit=None, marker=None):
        """Returns a list of the names of all users for this instance."""
        return self._user_manager.list(limit=limit, marker=marker)


    def get_user(self, name):
        """
        Finds the user in this instance with the specified name, and
        returns a CloudDatabaseUser object. If no match is found, a
        NoSuchDatabaseUser exception is raised.
        """
        try:
            return self._user_manager.get(name)
        except exc.NotFound:
            raise exc.NoSuchDatabaseUser("No user by the name '%s' exists." %
                    name)


    def get_database(self, name):
        """
        Finds the database in this instance with the specified name, and
        returns a CloudDatabaseDatabase object. If no match is found, a
        NoSuchDatabase exception is raised.
        """
        try:
            return [db for db in self.list_databases()
                    if db.name == name][0]
        except IndexError:
            raise exc.NoSuchDatabase("No database by the name '%s' exists." %
                    name)


    def create_database(self, name, character_set=None, collate=None):
        """
        Creates a database with the specified name. If a database with
        that name already exists, a BadRequest (400) exception will
        be raised.
        """
        if character_set is None:
            character_set = "utf8"
        if collate is None:
            collate = "utf8_general_ci"
        self._database_manager.create(name=name, character_set=character_set,
                collate=collate, return_none=True)
        # Since the API doesn't return the info for creating the database
        # object, we have to do it manually.
        return self._database_manager.find(name=name)


    def create_user(self, name, password, database_names, host=None):
        """
        Creates a user with the specified name and password, and gives that
        user access to the specified database(s).

        If a user with that name already exists, a BadRequest (400) exception
        will be raised.
        """
        if not isinstance(database_names, (list, tuple)):
            database_names = [database_names]
        # The API only accepts names, not DB objects
        database_names = [db if isinstance(db, six.string_types) else db.name
                for db in database_names]
        self._user_manager.create(name=name, password=password,
                database_names=database_names, host=host, return_none=True)
        # Since the API doesn't return the info for creating the user object,
        # we have to do it manually.
        return self._user_manager.find(name=name)


    def delete_database(self, name_or_obj):
        """
        Deletes the specified database. If no database by that name
        exists, no exception will be raised; instead, nothing at all
        is done.
        """
        name = utils.get_name(name_or_obj)
        self._database_manager.delete(name)


    def change_user_password(self, user, new_pass):
        """
        Changes the password for the user to the supplied value.

        Returns None upon success; raises PasswordChangeFailed if the call
        does not complete successfully.
        """
        return self._user_manager.change_user_password(user, new_pass)


    def update_user(self, user, name=None, password=None, host=None):
        """
        Allows you to change one or more of the user's username, password, or
        host.
        """
        return self._user_manager.update(user, name=name, password=password,
                host=host)


    def list_user_access(self, user):
        """
        Returns a list of all database names for which the specified user
        has access rights.
        """
        return self._user_manager.list_user_access(user)


    def grant_user_access(self, user, db_names, strict=True):
        """
        Gives access to the databases listed in `db_names` to the user.
        """
        return self._user_manager.grant_user_access(user, db_names,
                strict=strict)


    def revoke_user_access(self, user, db_names, strict=True):
        """
        Revokes access to the databases listed in `db_names` for the user.
        """
        return self._user_manager.revoke_user_access(user, db_names,
                strict=strict)


    def delete_user(self, user):
        """
        Deletes the specified user. If no user by that name
        exists, no exception will be raised; instead, nothing at all
        is done.
        """
        name = utils.get_name(user)
        self._user_manager.delete(name)


    def enable_root_user(self):
        """
        Enables login from any host for the root user and provides
        the user with a generated root password.
        """
        uri = "/instances/%s/root" % self.id
        resp, body = self.manager.api.method_post(uri)
        return body["user"]["password"]


    def root_user_status(self):
        """
        Returns True or False, depending on whether the root user
        for this instance has been enabled.
        """
        uri = "/instances/%s/root" % self.id
        resp, body = self.manager.api.method_get(uri)
        return body["rootEnabled"]


    def restart(self):
        """Restarts this instance."""
        self.manager.action(self, "restart")


    def resize(self, flavor):
        """Set the size of this instance to a different flavor."""
        # We need the flavorRef, not the flavor or size.
        flavorRef = self.manager.api._get_flavor_ref(flavor)
        body = {"flavorRef": flavorRef}
        self.manager.action(self, "resize", body=body)


    def resize_volume(self, size):
        """Changes the size of the volume for this instance."""
        curr_size = self.volume.size
        if size <= curr_size:
            raise exc.InvalidVolumeResize("The new volume size must be larger "
                    "than the current volume size of '%s'." % curr_size)
        body = {"volume": {"size": size}}
        self.manager.action(self, "resize", body=body)


    def list_backups(self):
        """
        Returns a list of all backups for this instance.
        """
        return self.manager._list_backups_for_instance(self)


    def create_backup(self, name, description=None):
        """
        Creates a backup of this instance, giving it the specified name along
        with an optional description.
        """
        return self.manager.create_backup(self, name, description=description)


    def _get_flavor(self):
        try:
            ret = self._flavor
        except AttributeError:
            ret = self._flavor = CloudDatabaseFlavor(
                    self.manager.api._flavor_manager, {})
        return ret

    def _set_flavor(self, flavor):
        if isinstance(flavor, dict):
            self._flavor = CloudDatabaseFlavor(self.manager.api._flavor_manager,
                    flavor)
        else:
            # Must be an instance
            self._flavor = flavor

    flavor = property(_get_flavor, _set_flavor)


class CloudDatabaseDatabase(BaseResource):
    """
    This class represents a database on a CloudDatabaseInstance. It is not
    a true cloud entity, but a convenience object for dealing with databases
    on instances.
    """
    get_details = True

    def delete(self):
        """This class doesn't have an 'id', so pass the name."""
        self.manager.delete(self.name)


class CloudDatabaseUser(BaseResource):
    """
    This class represents a user on a CloudDatabaseInstance. It is not
    a true cloud entity, but a convenience object for dealing with users
    for instances.
    """
    get_details = False
    name = None
    host = None

    def delete(self):
        """This class doesn't have an 'id', so pass the name."""
        self.manager.delete(self.name)


    def change_password(self, new_pass):
        """
        Changes the password for this user to the supplied value.

        Returns None upon success; raises PasswordChangeFailed if the call
        does not complete successfully.
        """
        self.manager.change_user_password(self, new_pass)


    def update(self, name=None, password=None, host=None):
        """
        Allows you to change one or more of the user's username, password, or
        host.
        """
        return self.manager.update(self, name=name, password=password,
                host=host)


    def list_user_access(self):
        """
        Returns a list of all database names for which the specified user
        has access rights.
        """
        return self.manager.list_user_access(self)


    def grant_user_access(self, db_names, strict=True):
        """
        Gives access to the databases listed in `db_names` to the user.
        """
        return self.manager.grant_user_access(self, db_names, strict=strict)


    def revoke_user_access(self, db_names, strict=True):
        """
        Revokes access to the databases listed in `db_names` for the user.
        """
        return self.manager.revoke_user_access(self, db_names, strict=strict)



class CloudDatabaseFlavor(BaseResource):
    """
    This class represents the available instance configurations, or 'flavors',
    which you use to define the memory and CPU size of your instance. These
    objects are read-only.
    """
    get_details = True
    _non_display = ["links"]



class CloudDatabaseBackup(BaseResource):
    """
    This class represents a database backup.
    """
    get_details = True
    _non_display = ["locationRef"]



class CloudDatabaseClient(BaseClient):
    """
    This is the primary class for interacting with Cloud Databases.
    """
    name = "Cloud Databases"

    def _configure_manager(self):
        """
        Creates a manager to handle the instances, and another
        to handle flavors.
        """
        self._manager = CloudDatabaseManager(self,
                resource_class=CloudDatabaseInstance, response_key="instance",
                uri_base="instances")
        self._flavor_manager = BaseManager(self,
                resource_class=CloudDatabaseFlavor, response_key="flavor",
                uri_base="flavors")
        self._backup_manager = CloudDatabaseBackupManager(self,
                resource_class=CloudDatabaseBackup, response_key="backup",
                uri_base="backups")


    @assure_instance
    def list_databases(self, instance, limit=None, marker=None):
        """Returns all databases for the specified instance."""
        return instance.list_databases(limit=limit, marker=marker)


    @assure_instance
    def create_database(self, instance, name, character_set=None,
            collate=None):
        """Creates a database with the specified name on the given instance."""
        return instance.create_database(name, character_set=character_set,
                collate=collate)


    @assure_instance
    def get_database(self, instance, name):
        """
        Finds the database in the given instance with the specified name, and
        returns a CloudDatabaseDatabase object. If no match is found, a
        NoSuchDatabase exception is raised.
        """
        return instance.get_database(name)


    @assure_instance
    def delete_database(self, instance, name):
        """Deletes the database by name on the given instance."""
        return instance.delete_database(name)


    @assure_instance
    def list_users(self, instance, limit=None, marker=None):
        """Returns all users for the specified instance."""
        return instance.list_users(limit=limit, marker=marker)


    @assure_instance
    def create_user(self, instance, name, password, database_names, host=None):
        """
        Creates a user with the specified name and password, and gives that
        user access to the specified database(s).
        """
        return instance.create_user(name=name, password=password,
                database_names=database_names, host=host)


    @assure_instance
    def get_user(self, instance, name):
        """
        Finds the user in the given instance with the specified name, and
        returns a CloudDatabaseUser object. If no match is found, a
        NoSuchUser exception is raised.
        """
        return instance.get_user(name)


    @assure_instance
    def delete_user(self, instance, name):
        """Deletes the user by name on the given instance."""
        return instance.delete_user(name)


    @assure_instance
    def change_user_password(self, instance, user, new_pass):
        """
        Changes the password for the user of the specified instance to the
        supplied value.

        Returns None upon success; raises PasswordChangeFailed if the call
        does not complete successfully.
        """
        return instance.change_user_password(user, new_pass)


    @assure_instance
    def update_user(self, instance, user, name=None, password=None, host=None):
        """
        Allows you to change one or more of the user's username, password, or
        host.
        """
        return instance.update_user(user, name=name, password=password,
                host=host)


    @assure_instance
    def list_user_access(self, instance, user):
        """
        Returns a list of all database names for which the specified user
        has access rights on the specified instance.
        """
        return instance.list_user_access(user)


    @assure_instance
    def grant_user_access(self, instance, user, db_names, strict=True):
        """
        Gives access to the databases listed in `db_names` to the user
        on the specified instance.
        """
        return instance.grant_user_access(user, db_names, strict=strict)


    @assure_instance
    def revoke_user_access(self, instance, user, db_names, strict=True):
        """
        Revokes access to the databases listed in `db_names` for the user
        on the specified instance.
        """
        return instance.revoke_user_access(user, db_names, strict=strict)


    @assure_instance
    def enable_root_user(self, instance):
        """
        This enables login from any host for the root user and provides
        the user with a generated root password.
        """
        return instance.enable_root_user()


    @assure_instance
    def root_user_status(self, instance):
        """Returns True if the given instance is root-enabled."""
        return instance.root_user_status()


    @assure_instance
    def restart(self, instance):
        """Restarts the instance."""
        return instance.restart()


    @assure_instance
    def resize(self, instance, flavor):
        """Sets the size of the instance to a different flavor."""
        return instance.resize(flavor)


    def get_limits(self):
        """Not implemented in Cloud Databases."""
        raise NotImplementedError("Limits are not available for Cloud Databases")


    def list_flavors(self, limit=None, marker=None):
        """Returns a list of all available Flavors."""
        return self._flavor_manager.list(limit=limit, marker=marker)


    def get_flavor(self, flavor_id):
        """Returns a specific Flavor object by ID."""
        return self._flavor_manager.get(flavor_id)


    def _get_flavor_ref(self, flavor):
        """
        Flavors are odd in that the API expects an href link, not an ID, as with
        nearly every other resource. This method takes either a
        CloudDatabaseFlavor object, a flavor ID, a RAM size, or a flavor name,
        and uses that to determine the appropriate href.
        """
        flavor_obj = None
        if isinstance(flavor, CloudDatabaseFlavor):
            flavor_obj = flavor
        elif isinstance(flavor, int):
            # They passed an ID or a size
            try:
                flavor_obj = self.get_flavor(flavor)
            except exc.NotFound:
                # Must be either a size or bad ID, which will
                # be handled below
                pass
        if flavor_obj is None:
            # Try flavor name
            flavors = self.list_flavors()
            try:
                flavor_obj = [flav for flav in flavors
                        if flav.name == flavor][0]
            except IndexError:
                # No such name; try matching RAM
                try:
                    flavor_obj = [flav for flav in flavors
                            if flav.ram == flavor][0]
                except IndexError:
                    raise exc.FlavorNotFound("Could not determine flavor from "
                            "'%s'." % flavor)
        # OK, we have a Flavor object. Get the href
        href = [link["href"] for link in flavor_obj.links
                if link["rel"] == "self"][0]
        return href


    def list_backups(self, instance=None):
        """
        Returns a list of all backups by default, or just for a particular
        instance.
        """
        return self._backup_manager.list(instance=instance)


    def get_backup(self, backup):
        """
        Returns the CloudDatabaseBackup instance for a given ID.
        """
        return self._backup_manager.get(backup)


    def delete_backup(self, backup):
        """
        Deletes the CloudDatabaseBackup instance for a given ID.
        """
        return self._backup_manager.delete(backup)


    @assure_instance
    def create_backup(self, instance, name, description=None):
        """
        Creates a backup of the specified instance, giving it the specified
        name along with an optional description.
        """
        return instance.create_backup(name, description=description)


    def restore_backup(self, backup, name, flavor, volume):
        """
        Restores a backup to a new database instance. You must supply a backup
        (either the ID or a CloudDatabaseBackup object), a name for the new
        instance, as well as a flavor and size (in GB) for the instance.
        """
        return self._manager.restore_backup(backup, name, flavor, volume)
