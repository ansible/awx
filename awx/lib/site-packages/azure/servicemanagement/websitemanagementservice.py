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
    _str,
    )
from azure.servicemanagement import (
    WebSpaces,
    WebSpace,
    Sites,
    Site,
    MetricResponses,
    MetricDefinitions,
    PublishData,
    _XmlSerializer,
    )
from azure.servicemanagement.servicemanagementclient import (
    _ServiceManagementClient,
    )

class WebsiteManagementService(_ServiceManagementClient):
    ''' Note that this class is a preliminary work on WebSite
        management. Since it lack a lot a features, final version
        can be slightly different from the current one.
    '''

    def __init__(self, subscription_id=None, cert_file=None,
                 host=MANAGEMENT_HOST, request_session=None):
        '''
        Initializes the website management service.

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
        super(WebsiteManagementService, self).__init__(
            subscription_id, cert_file, host, request_session)

    #--Operations for web sites ----------------------------------------
    def list_webspaces(self):
        '''
        List the webspaces defined on the account.
        '''
        return self._perform_get(self._get_list_webspaces_path(),
                                 WebSpaces)

    def get_webspace(self, webspace_name):
        '''
        Get details of a specific webspace.

        webspace_name: The name of the webspace.
        '''
        return self._perform_get(self._get_webspace_details_path(webspace_name),
                                 WebSpace)

    def list_sites(self, webspace_name):
        '''
        List the web sites defined on this webspace.

        webspace_name: The name of the webspace.
        '''
        return self._perform_get(self._get_sites_path(webspace_name),
                                 Sites)

    def get_site(self, webspace_name, website_name):
        '''
        List the web sites defined on this webspace.

        webspace_name: The name of the webspace.
        website_name: The name of the website.
        '''
        return self._perform_get(self._get_sites_details_path(webspace_name,
                                                              website_name),
                                 Site)

    def create_site(self, webspace_name, website_name, geo_region, host_names,
                    plan='VirtualDedicatedPlan', compute_mode='Shared',
                    server_farm=None, site_mode=None):
        '''
        Create a website.

        webspace_name: The name of the webspace.
        website_name: The name of the website.
        geo_region:
            The geographical region of the webspace that will be created.
        host_names:
            An array of fully qualified domain names for website. Only one
            hostname can be specified in the azurewebsites.net domain.
            The hostname should match the name of the website. Custom domains
            can only be specified for Shared or Standard websites.
        plan:
            This value must be 'VirtualDedicatedPlan'.
        compute_mode:
            This value should be 'Shared' for the Free or Paid Shared
            offerings, or 'Dedicated' for the Standard offering. The default
            value is 'Shared'. If you set it to 'Dedicated', you must specify
            a value for the server_farm parameter.
        server_farm:
            The name of the Server Farm associated with this website. This is
            a required value for Standard mode.
        site_mode:
            Can be None, 'Limited' or 'Basic'. This value is 'Limited' for the
            Free offering, and 'Basic' for the Paid Shared offering. Standard
            mode does not use the site_mode parameter; it uses the compute_mode
            parameter.
        '''
        xml = _XmlSerializer.create_website_to_xml(webspace_name, website_name, geo_region, plan, host_names, compute_mode, server_farm, site_mode)
        return self._perform_post(
            self._get_sites_path(webspace_name),
            xml,
            Site)

    def delete_site(self, webspace_name, website_name,
                    delete_empty_server_farm=False, delete_metrics=False):
        '''
        Delete a website.

        webspace_name: The name of the webspace.
        website_name: The name of the website.
        delete_empty_server_farm:
            If the site being deleted is the last web site in a server farm,
            you can delete the server farm by setting this to True.
        delete_metrics:
            To also delete the metrics for the site that you are deleting, you
            can set this to True.
        '''
        path = self._get_sites_details_path(webspace_name, website_name)
        query = ''
        if delete_empty_server_farm:
            query += '&deleteEmptyServerFarm=true'
        if delete_metrics:
            query += '&deleteMetrics=true'
        if query:
            path = path + '?' + query.lstrip('&')
        return self._perform_delete(path)

    def restart_site(self, webspace_name, website_name):
        '''
        Restart a web site.

        webspace_name: The name of the webspace.
        website_name: The name of the website.
        '''
        return self._perform_post(
            self._get_restart_path(webspace_name, website_name),
            '')

    def get_historical_usage_metrics(self, webspace_name, website_name,
                                     metrics = None, start_time=None, end_time=None, time_grain=None):
        '''
        Get historical usage metrics.

        webspace_name: The name of the webspace.
        website_name: The name of the website.
        metrics: Optional. List of metrics name. Otherwise, all metrics returned.
        start_time: Optional. An ISO8601 date. Otherwise, current hour is used.
        end_time: Optional. An ISO8601 date. Otherwise, current time is used.
        time_grain: Optional. A rollup name, as P1D. OTherwise, default rollup for the metrics is used.
        More information and metrics name at:
        http://msdn.microsoft.com/en-us/library/azure/dn166964.aspx
        '''        
        metrics = ('names='+','.join(metrics)) if metrics else ''
        start_time = ('StartTime='+start_time) if start_time else ''
        end_time = ('EndTime='+end_time) if end_time else ''
        time_grain = ('TimeGrain='+time_grain) if time_grain else ''
        parameters = ('&'.join(v for v in (metrics, start_time, end_time, time_grain) if v))
        parameters = '?'+parameters if parameters else ''
        return self._perform_get(self._get_historical_usage_metrics_path(webspace_name, website_name) + parameters,
                                 MetricResponses)

    def get_metric_definitions(self, webspace_name, website_name):
        '''
        Get metric definitions of metrics available of this web site.

        webspace_name: The name of the webspace.
        website_name: The name of the website.
        '''
        return self._perform_get(self._get_metric_definitions_path(webspace_name, website_name),
                                 MetricDefinitions)

    def get_publish_profile_xml(self, webspace_name, website_name):
        '''
        Get a site's publish profile as a string

        webspace_name: The name of the webspace.
        website_name: The name of the website.
        '''
        return self._perform_get(self._get_publishxml_path(webspace_name, website_name),
                                 None).body.decode("utf-8")

    def get_publish_profile(self, webspace_name, website_name):
        '''
        Get a site's publish profile as an object

        webspace_name: The name of the webspace.
        website_name: The name of the website.
        '''
        return self._perform_get(self._get_publishxml_path(webspace_name, website_name),
                                 PublishData)

    #--Helper functions --------------------------------------------------
    def _get_list_webspaces_path(self):
        return self._get_path('services/webspaces', None)

    def _get_webspace_details_path(self, webspace_name):
        return self._get_path('services/webspaces/', webspace_name)

    def _get_sites_path(self, webspace_name):
        return self._get_path('services/webspaces/',
                              webspace_name) + '/sites'

    def _get_sites_details_path(self, webspace_name, website_name):
        return self._get_path('services/webspaces/',
                              webspace_name) + '/sites/' + _str(website_name)

    def _get_restart_path(self, webspace_name, website_name):
        return self._get_path('services/webspaces/',
                              webspace_name) + '/sites/' + _str(website_name) + '/restart/' 

    def _get_historical_usage_metrics_path(self, webspace_name, website_name):
        return self._get_path('services/webspaces/',
                              webspace_name) + '/sites/' + _str(website_name) + '/metrics/' 
                               
    def _get_metric_definitions_path(self, webspace_name, website_name):
        return self._get_path('services/webspaces/',
                              webspace_name) + '/sites/' + _str(website_name) + '/metricdefinitions/' 

    def _get_publishxml_path(self, webspace_name, website_name):
        return self._get_path('services/webspaces/',
                              webspace_name) + '/sites/' + _str(website_name) + '/publishxml/' 
