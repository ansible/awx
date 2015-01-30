#-------------------------------------------------------------------------
# Copyright (c) Microsoft.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#--------------------------------------------------------------------------
from azure import (
    MANAGEMENT_HOST,
    _parse_service_resources_response,
    _validate_not_none,
    )
from azure.servicemanagement import (
    EventLog,
    ServerQuota,
    Servers,
    ServiceObjective,
    Database,
    FirewallRule,
    _SqlManagementXmlSerializer,
    )
from azure.servicemanagement.servicemanagementclient import (
    _ServiceManagementClient,
    )

class SqlDatabaseManagementService(_ServiceManagementClient):
    ''' Note that this class is a preliminary work on SQL Database
        management. Since it lack a lot a features, final version
        can be slightly different from the current one.
    '''

    def __init__(self, subscription_id=None, cert_file=None,
                 host=MANAGEMENT_HOST, request_session=None):
        '''
        Initializes the sql database management service.

        subscription_id: Subscription to manage.
        cert_file:
            Path to .pem certificate file (httplib), or location of the
            certificate in your Personal certificate store (winhttp) in the
            CURRENT_USER\my\CertificateName format.
            If a request_session is specified, then this is unused.
        host: Live ServiceClient URL. Defaults to Azure public cloud.
        request_session:
            Session object to use for http requests. If this is specified, it
            replaces the default use of httplib or winhttp. Also, the cert_file
            parameter is unused when a session is passed in.
            The session object handles authentication, and as such can support
            multiple types of authentication: .pem certificate, oauth.
            For example, you can pass in a Session instance from the requests
            library. To use .pem certificate authentication with requests
            library, set the path to the .pem file on the session.cert
            attribute.
        '''
        super(SqlDatabaseManagementService, self).__init__(
            subscription_id, cert_file, host, request_session)
        self.content_type = 'application/xml'

    #--Operations for sql servers ----------------------------------------
    def create_server(self, admin_login, admin_password, location):
        '''
        Create a new Azure SQL Database server.

        admin_login: The administrator login name for the new server.
        admin_password: The administrator login password for the new server.
        location: The region to deploy the new server.
        '''
        _validate_not_none('admin_login', admin_login)
        _validate_not_none('admin_password', admin_password)
        _validate_not_none('location', location)
        response = self.perform_post(
            self._get_servers_path(),
            _SqlManagementXmlSerializer.create_server_to_xml(
                admin_login,
                admin_password,
                location
            )
        )

        return _SqlManagementXmlSerializer.xml_to_create_server_response(
            response.body)

    def set_server_admin_password(self, server_name, admin_password):
        '''
        Reset the administrator password for a server.

        server_name: Name of the server to change the password.
        admin_password: The new administrator password for the server.
        '''
        _validate_not_none('server_name', server_name)
        _validate_not_none('admin_password', admin_password)
        return self._perform_post(
            self._get_servers_path(server_name) + '?op=ResetPassword',
            _SqlManagementXmlSerializer.set_server_admin_password_to_xml(
                admin_password
            )
        )

    def delete_server(self, server_name):
        '''
        Deletes an Azure SQL Database server (including all its databases).

        server_name: Name of the server you want to delete.
        '''
        _validate_not_none('server_name', server_name)
        return self._perform_delete(
            self._get_servers_path(server_name))

    def list_servers(self):
        '''
        List the SQL servers defined on the account.
        '''
        return self._perform_get(self._get_servers_path(),
                                 Servers)

    def list_quotas(self, server_name):
        '''
        Gets quotas for an Azure SQL Database Server.

        server_name: Name of the server.
        '''
        _validate_not_none('server_name', server_name)
        response = self._perform_get(self._get_quotas_path(server_name),
                                     None)
        return _parse_service_resources_response(response, ServerQuota)

    def get_server_event_logs(self, server_name, start_date,
                              interval_size_in_minutes, event_types=''):
        '''
        Gets the event logs for an Azure SQL Database Server.

        server_name: Name of the server to retrieve the event logs from.
        start_date:
            The starting date and time of the events to retrieve in UTC format,
            for example '2011-09-28 16:05:00'.
        interval_size_in_minutes:
            Size of the event logs to retrieve (in minutes).
            Valid values are: 5, 60, or 1440.
        event_types:
            The event type of the log entries you want to retrieve.
            Valid values are: 
                - connection_successful
                - connection_failed
                - connection_terminated
                - deadlock
                - throttling
                - throttling_long_transaction
            To return all event types pass in an empty string.
        '''
        _validate_not_none('server_name', server_name)
        _validate_not_none('start_date', start_date)
        _validate_not_none('interval_size_in_minutes', interval_size_in_minutes)
        _validate_not_none('event_types', event_types)
        path = self._get_server_event_logs_path(server_name) + \
               '?startDate={0}&intervalSizeInMinutes={1}&eventTypes={2}'.format(
            start_date, interval_size_in_minutes, event_types)
        response = self._perform_get(path, None)
        return _parse_service_resources_response(response, EventLog)

    #--Operations for firewall rules ------------------------------------------
    def create_firewall_rule(self, server_name, name, start_ip_address,
                             end_ip_address):
        '''
        Creates an Azure SQL Database server firewall rule.

        server_name: Name of the server to set the firewall rule on. 
        name: The name of the new firewall rule.
        start_ip_address:
            The lowest IP address in the range of the server-level firewall
            setting. IP addresses equal to or greater than this can attempt to
            connect to the server. The lowest possible IP address is 0.0.0.0.
        end_ip_address:
            The highest IP address in the range of the server-level firewall
            setting. IP addresses equal to or less than this can attempt to
            connect to the server. The highest possible IP address is
            255.255.255.255.
        '''
        _validate_not_none('server_name', server_name)
        _validate_not_none('name', name)
        _validate_not_none('start_ip_address', start_ip_address)
        _validate_not_none('end_ip_address', end_ip_address)
        return self._perform_post(
            self._get_firewall_rules_path(server_name),
            _SqlManagementXmlSerializer.create_firewall_rule_to_xml(
                name, start_ip_address, end_ip_address
            )
        )

    def update_firewall_rule(self, server_name, name, start_ip_address,
                             end_ip_address):
        '''
        Update a firewall rule for an Azure SQL Database server.

        server_name: Name of the server to set the firewall rule on. 
        name: The name of the firewall rule to update.
        start_ip_address:
            The lowest IP address in the range of the server-level firewall
            setting. IP addresses equal to or greater than this can attempt to
            connect to the server. The lowest possible IP address is 0.0.0.0.
        end_ip_address:
            The highest IP address in the range of the server-level firewall
            setting. IP addresses equal to or less than this can attempt to
            connect to the server. The highest possible IP address is
            255.255.255.255.
        '''
        _validate_not_none('server_name', server_name)
        _validate_not_none('name', name)
        _validate_not_none('start_ip_address', start_ip_address)
        _validate_not_none('end_ip_address', end_ip_address)
        return self._perform_put(
            self._get_firewall_rules_path(server_name, name),
            _SqlManagementXmlSerializer.update_firewall_rule_to_xml(
                name, start_ip_address, end_ip_address
            )
        )

    def delete_firewall_rule(self, server_name, name):
        '''
        Deletes an Azure SQL Database server firewall rule.

        server_name:
            Name of the server with the firewall rule you want to delete.
        name:
            Name of the firewall rule you want to delete.
        '''
        _validate_not_none('server_name', server_name)
        _validate_not_none('name', name)
        return self._perform_delete(
            self._get_firewall_rules_path(server_name, name))

    def list_firewall_rules(self, server_name):
        '''
        Retrieves the set of firewall rules for an Azure SQL Database Server.

        server_name: Name of the server.
        '''
        _validate_not_none('server_name', server_name)
        response = self._perform_get(self._get_firewall_rules_path(server_name),
                                     None)
        return _parse_service_resources_response(response, FirewallRule)

    def list_service_level_objectives(self, server_name):
        '''
        Gets the service level objectives for an Azure SQL Database server.

        server_name: Name of the server.
        '''
        _validate_not_none('server_name', server_name)
        response = self._perform_get(
            self._get_service_objectives_path(server_name), None)
        return _parse_service_resources_response(response, ServiceObjective)

    #--Operations for sql databases ----------------------------------------
    def create_database(self, server_name, name, service_objective_id,
                        edition=None, collation_name=None,
                        max_size_bytes=None):
        '''
        Creates a new Azure SQL Database.

        server_name: Name of the server to contain the new database.
        name:
            Required. The name for the new database. See Naming Requirements
            in Azure SQL Database General Guidelines and Limitations and
            Database Identifiers for more information.
        service_objective_id:
            Required. The GUID corresponding to the performance level for
            Edition. See List Service Level Objectives for current values.
        edition:
            Optional. The Service Tier (Edition) for the new database. If
            omitted, the default is Web. Valid values are Web, Business,
            Basic, Standard, and Premium. See Azure SQL Database Service Tiers
            (Editions) and Web and Business Edition Sunset FAQ for more
            information.
        collation_name:
            Optional. The database collation. This can be any collation
            supported by SQL. If omitted, the default collation is used. See
            SQL Server Collation Support in Azure SQL Database General
            Guidelines and Limitations for more information.
        max_size_bytes:
            Optional. Sets the maximum size, in bytes, for the database. This
            value must be within the range of allowed values for Edition. If
            omitted, the default value for the edition is used. See Azure SQL
            Database Service Tiers (Editions) for current maximum databases
            sizes. Convert MB or GB values to bytes.
            1 MB = 1048576 bytes. 1 GB = 1073741824 bytes.
        '''
        _validate_not_none('server_name', server_name)
        _validate_not_none('name', name)
        _validate_not_none('service_objective_id', service_objective_id)
        return self._perform_post(
            self._get_databases_path(server_name),
            _SqlManagementXmlSerializer.create_database_to_xml(
                name, service_objective_id, edition, collation_name,
                max_size_bytes
            )
        )

    def update_database(self, server_name, name, new_database_name=None,
                        service_objective_id=None, edition=None,
                        max_size_bytes=None):
        '''
        Updates existing database details.

        server_name: Name of the server to contain the new database.
        name:
            Required. The name for the new database. See Naming Requirements
            in Azure SQL Database General Guidelines and Limitations and
            Database Identifiers for more information.
        new_database_name:
            Optional. The new name for the new database.
        service_objective_id:
            Optional. The new service level to apply to the database. For more
            information about service levels, see Azure SQL Database Service
            Tiers and Performance Levels. Use List Service Level Objectives to
            get the correct ID for the desired service objective.
        edition:
            Optional. The new edition for the new database.
        max_size_bytes:
            Optional. The new size of the database in bytes. For information on
            available sizes for each edition, see Azure SQL Database Service
            Tiers (Editions).
        '''
        _validate_not_none('server_name', server_name)
        _validate_not_none('name', name)
        return self._perform_put(
            self._get_databases_path(server_name, name),
            _SqlManagementXmlSerializer.update_database_to_xml(
                new_database_name, service_objective_id, edition,
                max_size_bytes
            )
        )

    def delete_database(self, server_name, name):
        '''
        Deletes an Azure SQL Database.

        server_name: Name of the server where the database is located.
        name: Name of the database to delete.
        '''
        return self._perform_delete(self._get_databases_path(server_name, name))

    def list_databases(self, name):
        '''
        List the SQL databases defined on the specified server name
        '''
        response = self._perform_get(self._get_list_databases_path(name),
                                     None)
        return _parse_service_resources_response(response, Database)


    #--Helper functions --------------------------------------------------
    def _get_servers_path(self, server_name=None):
        return self._get_path('services/sqlservers/servers', server_name)

    def _get_firewall_rules_path(self, server_name, name=None):
        path = self._get_servers_path(server_name) + '/firewallrules'
        if name:
            path = path + '/' + name
        return path

    def _get_databases_path(self, server_name, name=None):
        path = self._get_servers_path(server_name) + '/databases'
        if name:
            path = path + '/' + name
        return path

    def _get_server_event_logs_path(self, server_name):
        return self._get_servers_path(server_name) + '/events'

    def _get_service_objectives_path(self, server_name):
        return self._get_servers_path(server_name) + '/serviceobjectives'

    def _get_quotas_path(self, server_name, name=None):
        path = self._get_servers_path(server_name) + '/serverquotas'
        if name:
            path = path + '/' + name
        return path

    def _get_list_databases_path(self, name):
        # *contentview=generic is mandatory*
        return self._get_path('services/sqlservers/servers/',
                              name) + '/databases?contentview=generic' 

