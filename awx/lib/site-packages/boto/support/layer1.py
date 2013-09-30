# Copyright (c) 2013 Amazon.com, Inc. or its affiliates.  All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#

import json
import boto
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.support import exceptions


class SupportConnection(AWSQueryConnection):
    """
    AWS Support
    The AWS Support API reference is intended for programmers who need
    detailed information about the AWS Support actions and data types.
    This service enables you to manage with your AWS Support cases
    programmatically. It is built on the AWS Query API programming
    model and provides HTTP methods that take parameters and return
    results in JSON format.

    The AWS Support service also exposes a set of `Trusted Advisor`_
    features. You can retrieve a list of checks you can run on your
    resources, specify checks to run and refresh, and check the status
    of checks you have submitted.

    The following list describes the AWS Support case management
    actions:


    + **Service names, issue categories, and available severity
      levels. **The actions `DescribeServices`_ and
      `DescribeSeverityLevels`_ enable you to obtain AWS service names,
      service codes, service categories, and problem severity levels.
      You use these values when you call the `CreateCase`_ action.
    + **Case Creation, case details, and case resolution**. The
      actions `CreateCase`_, `DescribeCases`_, and `ResolveCase`_ enable
      you to create AWS Support cases, retrieve them, and resolve them.
    + **Case communication**. The actions
      `DescribeCaseCommunications`_ and `AddCommunicationToCase`_ enable
      you to retrieve and add communication to AWS Support cases.


    The following list describes the actions available from the AWS
    Support service for Trusted Advisor:


    + `DescribeTrustedAdviserChecks`_    returns the list of checks that you can run against your AWS
    resources.
    + Using the CheckId for a specific check returned by
      DescribeTrustedAdviserChecks, you can call
      `DescribeTrustedAdvisorCheckResult`_    and obtain a new result for the check you specified.
    + Using `DescribeTrustedAdvisorCheckSummaries`_, you can get
      summaries for a set of Trusted Advisor checks.
    + `RefreshTrustedAdvisorCheck`_ enables you to request that
      Trusted Advisor run the check again.
    + ``_ gets statuses on the checks you are running.


    For authentication of requests, the AWS Support uses `Signature
    Version 4 Signing Process`_.

    See the AWS Support Developer Guide for information about how to
    use this service to manage create and manage your support cases,
    and how to call Trusted Advisor for results of checks on your
    resources.
    """
    APIVersion = "2013-04-15"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "support.us-east-1.amazonaws.com"
    ServiceName = "Support"
    TargetPrefix = "AWSSupport_20130415"
    ResponseError = JSONResponseError

    _faults = {
        "CaseIdNotFound": exceptions.CaseIdNotFound,
        "CaseCreationLimitExceeded": exceptions.CaseCreationLimitExceeded,
        "InternalServerError": exceptions.InternalServerError,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)
        kwargs['host'] = region.endpoint
        AWSQueryConnection.__init__(self, **kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def add_communication_to_case(self, communication_body, case_id=None,
                                  cc_email_addresses=None):
        """
        This action adds additional customer communication to an AWS
        Support case. You use the CaseId value to identify the case to
        which you want to add communication. You can list a set of
        email addresses to copy on the communication using the
        CcEmailAddresses value. The CommunicationBody value contains
        the text of the communication.

        This action's response indicates the success or failure of the
        request.

        This action implements a subset of the behavior on the AWS
        Support `Your Support Cases`_ web form.

        :type case_id: string
        :param case_id:

        :type communication_body: string
        :param communication_body:

        :type cc_email_addresses: list
        :param cc_email_addresses:

        """
        params = {'communicationBody': communication_body, }
        if case_id is not None:
            params['caseId'] = case_id
        if cc_email_addresses is not None:
            params['ccEmailAddresses'] = cc_email_addresses
        return self.make_request(action='AddCommunicationToCase',
                                 body=json.dumps(params))

    def create_case(self, subject, service_code, category_code,
                    communication_body, severity_code=None,
                    cc_email_addresses=None, language=None, issue_type=None):
        """
        Creates a new case in the AWS Support Center. This action is
        modeled on the behavior of the AWS Support Center `Open a new
        case`_ page. Its parameters require you to specify the
        following information:


        #. **ServiceCode.** Represents a code for an AWS service. You
           obtain the ServiceCode by calling `DescribeServices`_.
        #. **CategoryCode**. Represents a category for the service
           defined for the ServiceCode value. You also obtain the
           cateogory code for a service by calling `DescribeServices`_.
           Each AWS service defines its own set of category codes.
        #. **SeverityCode**. Represents a value that specifies the
           urgency of the case, and the time interval in which your
           service level agreement specifies a response from AWS Support.
           You obtain the SeverityCode by calling
           `DescribeSeverityLevels`_.
        #. **Subject**. Represents the **Subject** field on the AWS
           Support Center `Open a new case`_ page.
        #. **CommunicationBody**. Represents the **Description** field
           on the AWS Support Center `Open a new case`_ page.
        #. **Language**. Specifies the human language in which AWS
           Support handles the case. The API currently supports English
           and Japanese.
        #. **CcEmailAddresses**. Represents the AWS Support Center
           **CC** field on the `Open a new case`_ page. You can list
           email addresses to be copied on any correspondence about the
           case. The account that opens the case is already identified by
           passing the AWS Credentials in the HTTP POST method or in a
           method or function call from one of the programming languages
           supported by an `AWS SDK`_.


        The AWS Support API does not currently support the ability to
        add attachments to cases. You can, however, call
        `AddCommunicationToCase`_ to add information to an open case.

        A successful `CreateCase`_ request returns an AWS Support case
        number. Case numbers are used by `DescribeCases`_ request to
        retrieve existing AWS Support support cases.

        :type subject: string
        :param subject:

        :type service_code: string
        :param service_code:

        :type severity_code: string
        :param severity_code:

        :type category_code: string
        :param category_code:

        :type communication_body: string
        :param communication_body:

        :type cc_email_addresses: list
        :param cc_email_addresses:

        :type language: string
        :param language:

        :type issue_type: string
        :param issue_type:

        """
        params = {
            'subject': subject,
            'serviceCode': service_code,
            'categoryCode': category_code,
            'communicationBody': communication_body,
        }
        if severity_code is not None:
            params['severityCode'] = severity_code
        if cc_email_addresses is not None:
            params['ccEmailAddresses'] = cc_email_addresses
        if language is not None:
            params['language'] = language
        if issue_type is not None:
            params['issueType'] = issue_type
        return self.make_request(action='CreateCase',
                                 body=json.dumps(params))

    def describe_cases(self, case_id_list=None, display_id=None,
                       after_time=None, before_time=None,
                       include_resolved_cases=None, next_token=None,
                       max_results=None, language=None):
        """
        This action returns a list of cases that you specify by
        passing one or more CaseIds. In addition, you can filter the
        cases by date by setting values for the AfterTime and
        BeforeTime request parameters.
        The response returns the following in JSON format:

        #. One or more `CaseDetails`_ data types.
        #. One or more NextToken objects, strings that specifies where
           to paginate the returned records represented by CaseDetails .

        :type case_id_list: list
        :param case_id_list:

        :type display_id: string
        :param display_id:

        :type after_time: string
        :param after_time:

        :type before_time: string
        :param before_time:

        :type include_resolved_cases: boolean
        :param include_resolved_cases:

        :type next_token: string
        :param next_token:

        :type max_results: integer
        :param max_results:

        :type language: string
        :param language:

        """
        params = {}
        if case_id_list is not None:
            params['caseIdList'] = case_id_list
        if display_id is not None:
            params['displayId'] = display_id
        if after_time is not None:
            params['afterTime'] = after_time
        if before_time is not None:
            params['beforeTime'] = before_time
        if include_resolved_cases is not None:
            params['includeResolvedCases'] = include_resolved_cases
        if next_token is not None:
            params['nextToken'] = next_token
        if max_results is not None:
            params['maxResults'] = max_results
        if language is not None:
            params['language'] = language
        return self.make_request(action='DescribeCases',
                                 body=json.dumps(params))

    def describe_communications(self, case_id, before_time=None,
                                after_time=None, next_token=None,
                                max_results=None):
        """
        This action returns communications regarding the support case.
        You can use the AfterTime and BeforeTime parameters to filter
        by date. The CaseId parameter enables you to identify a
        specific case by its CaseId number.

        The MaxResults and NextToken parameters enable you to control
        the pagination of the result set. Set MaxResults to the number
        of cases you want displayed on each page, and use NextToken to
        specify the resumption of pagination.

        :type case_id: string
        :param case_id:

        :type before_time: string
        :param before_time:

        :type after_time: string
        :param after_time:

        :type next_token: string
        :param next_token:

        :type max_results: integer
        :param max_results:

        """
        params = {'caseId': case_id, }
        if before_time is not None:
            params['beforeTime'] = before_time
        if after_time is not None:
            params['afterTime'] = after_time
        if next_token is not None:
            params['nextToken'] = next_token
        if max_results is not None:
            params['maxResults'] = max_results
        return self.make_request(action='DescribeCommunications',
                                 body=json.dumps(params))

    def describe_services(self, service_code_list=None, language=None):
        """
        Returns the current list of AWS services and a list of service
        categories that applies to each one. You then use service
        names and categories in your `CreateCase`_ requests. Each AWS
        service has its own set of categories.

        The service codes and category codes correspond to the values
        that are displayed in the **Service** and **Category** drop-
        down lists on the AWS Support Center `Open a new case`_ page.
        The values in those fields, however, do not necessarily match
        the service codes and categories returned by the
        `DescribeServices` request. Always use the service codes and
        categories obtained programmatically. This practice ensures
        that you always have the most recent set of service and
        category codes.

        :type service_code_list: list
        :param service_code_list:

        :type language: string
        :param language:

        """
        params = {}
        if service_code_list is not None:
            params['serviceCodeList'] = service_code_list
        if language is not None:
            params['language'] = language
        return self.make_request(action='DescribeServices',
                                 body=json.dumps(params))

    def describe_severity_levels(self, language=None):
        """
        This action returns the list of severity levels that you can
        assign to an AWS Support case. The severity level for a case
        is also a field in the `CaseDetails`_ data type included in
        any `CreateCase`_ request.

        :type language: string
        :param language:

        """
        params = {}
        if language is not None:
            params['language'] = language
        return self.make_request(action='DescribeSeverityLevels',
                                 body=json.dumps(params))

    def resolve_case(self, case_id=None):
        """
        Takes a CaseId and returns the initial state of the case along
        with the state of the case after the call to `ResolveCase`_
        completed.

        :type case_id: string
        :param case_id:

        """
        params = {}
        if case_id is not None:
            params['caseId'] = case_id
        return self.make_request(action='ResolveCase',
                                 body=json.dumps(params))

    def describe_trusted_advisor_check_refresh_statuses(self, check_ids):
        """
        Returns the status of all refresh requests Trusted Advisor
        checks called using `RefreshTrustedAdvisorCheck`_.

        :type check_ids: list
        :param check_ids:

        """
        params = {'checkIds': check_ids, }
        return self.make_request(action='DescribeTrustedAdvisorCheckRefreshStatuses',
                                 body=json.dumps(params))

    def describe_trusted_advisor_check_result(self, check_id, language=None):
        """
        This action responds with the results of a Trusted Advisor
        check. Once you have obtained the list of available Trusted
        Advisor checks by calling `DescribeTrustedAdvisorChecks`_, you
        specify the CheckId for the check you want to retrieve from
        AWS Support.

        The response for this action contains a JSON-formatted
        `TrustedAdvisorCheckResult`_ object
        , which is a container for the following three objects:



        #. `TrustedAdvisorCategorySpecificSummary`_
        #. `TrustedAdvisorResourceDetail`_
        #. `TrustedAdvisorResourcesSummary`_


        In addition, the response contains the following fields:


        #. **Status**. Overall status of the check.
        #. **Timestamp**. Time at which Trusted Advisor last ran the
           check.
        #. **CheckId**. Unique identifier for the specific check
           returned by the request.

        :type check_id: string
        :param check_id:

        :type language: string
        :param language:

        """
        params = {'checkId': check_id, }
        if language is not None:
            params['language'] = language
        return self.make_request(action='DescribeTrustedAdvisorCheckResult',
                                 body=json.dumps(params))

    def describe_trusted_advisor_check_summaries(self, check_ids):
        """
        This action enables you to get the latest summaries for
        Trusted Advisor checks that you specify in your request. You
        submit the list of Trusted Advisor checks for which you want
        summaries. You obtain these CheckIds by submitting a
        `DescribeTrustedAdvisorChecks`_ request.

        The response body contains an array of
        `TrustedAdvisorCheckSummary`_ objects.

        :type check_ids: list
        :param check_ids:

        """
        params = {'checkIds': check_ids, }
        return self.make_request(action='DescribeTrustedAdvisorCheckSummaries',
                                 body=json.dumps(params))

    def describe_trusted_advisor_checks(self, language):
        """
        This action enables you to get a list of the available Trusted
        Advisor checks. You must specify a language code. English
        ("en") and Japanese ("jp") are currently supported. The
        response contains a list of `TrustedAdvisorCheckDescription`_
        objects.

        :type language: string
        :param language:

        """
        params = {'language': language, }
        return self.make_request(action='DescribeTrustedAdvisorChecks',
                                 body=json.dumps(params))

    def refresh_trusted_advisor_check(self, check_id):
        """
        This action enables you to query the service to request a
        refresh for a specific Trusted Advisor check. Your request
        body contains a CheckId for which you are querying. The
        response body contains a `RefreshTrustedAdvisorCheckResult`_
        object containing Status and TimeUntilNextRefresh fields.

        :type check_id: string
        :param check_id:

        """
        params = {'checkId': check_id, }
        return self.make_request(action='RefreshTrustedAdvisorCheck',
                                 body=json.dumps(params))

    def make_request(self, action, body):
        headers = {
            'X-Amz-Target': '%s.%s' % (self.TargetPrefix, action),
            'Host': self.region.endpoint,
            'Content-Type': 'application/x-amz-json-1.1',
            'Content-Length': str(len(body)),
        }
        http_request = self.build_base_http_request(
            method='POST', path='/', auth_path='/', params={},
            headers=headers, data=body)
        response = self._mexe(http_request, sender=None,
                              override_num_retries=10)
        response_body = response.read()
        boto.log.debug(response_body)
        if response.status == 200:
            if response_body:
                return json.loads(response_body)
        else:
            json_body = json.loads(response_body)
            fault_name = json_body.get('__type', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)

