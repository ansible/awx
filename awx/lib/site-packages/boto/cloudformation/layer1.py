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

try:
    import json
except ImportError:
    import simplejson as json

import boto
from boto.connection import AWSQueryConnection
from boto.regioninfo import RegionInfo
from boto.exception import JSONResponseError
from boto.cloudformation import exceptions


class CloudFormationConnection(AWSQueryConnection):
    """
    AWS CloudFormation
    AWS CloudFormation enables you to create and manage AWS
    infrastructure deployments predictably and repeatedly. AWS
    CloudFormation helps you leverage AWS products such as Amazon EC2,
    EBS, Amazon SNS, ELB, and Auto Scaling to build highly-reliable,
    highly scalable, cost effective applications without worrying
    about creating and configuring the underlying AWS infrastructure.

    With AWS CloudFormation, you declare all of your resources and
    dependencies in a template file. The template defines a collection
    of resources as a single unit called a stack. AWS CloudFormation
    creates and deletes all member resources of the stack together and
    manages all dependencies between the resources for you.

    For more information about this product, go to the `CloudFormation
    Product Page`_.

    Amazon CloudFormation makes use of other AWS products. If you need
    additional technical information about a specific AWS product, you
    can find the product's technical documentation at
    `http://aws.amazon.com/documentation/`_.
    """
    APIVersion = "2010-05-15"
    DefaultRegionName = "us-east-1"
    DefaultRegionEndpoint = "cloudformation.us-east-1.amazonaws.com"
    ResponseError = JSONResponseError

    _faults = {
        "AlreadyExistsException": exceptions.AlreadyExistsException,
        "InsufficientCapabilitiesException": exceptions.InsufficientCapabilitiesException,
        "LimitExceededException": exceptions.LimitExceededException,
    }


    def __init__(self, **kwargs):
        region = kwargs.pop('region', None)
        if not region:
            region = RegionInfo(self, self.DefaultRegionName,
                                self.DefaultRegionEndpoint)

        if 'host' not in kwargs:
            kwargs['host'] = region.endpoint

        super(CloudFormationConnection, self).__init__(**kwargs)
        self.region = region

    def _required_auth_capability(self):
        return ['hmac-v4']

    def cancel_update_stack(self, stack_name):
        """
        Cancels an update on the specified stack. If the call
        completes successfully, the stack will roll back the update
        and revert to the previous stack configuration.
        Only stacks that are in the UPDATE_IN_PROGRESS state can be
        canceled.

        :type stack_name: string
        :param stack_name: The name or the unique identifier associated with
            the stack.

        """
        params = {'StackName': stack_name, }
        return self._make_request(
            action='CancelUpdateStack',
            verb='POST',
            path='/', params=params)

    def create_stack(self, stack_name, template_body=None, template_url=None,
                     parameters=None, disable_rollback=None,
                     timeout_in_minutes=None, notification_arns=None,
                     capabilities=None, on_failure=None,
                     stack_policy_body=None, stack_policy_url=None,
                     tags=None):
        """
        Creates a stack as specified in the template. After the call
        completes successfully, the stack creation starts. You can
        check the status of the stack via the DescribeStacks API.
        Currently, the limit for stacks is 20 stacks per account per
        region.

        :type stack_name: string
        :param stack_name:
        The name associated with the stack. The name must be unique within your
            AWS account.

        Must contain only alphanumeric characters (case sensitive) and start
            with an alpha character. Maximum length of the name is 255
            characters.

        :type template_body: string
        :param template_body: Structure containing the template body. (For more
            information, go to `Template Anatomy`_ in the AWS CloudFormation
            User Guide.)
        Conditional: You must pass `TemplateBody` or `TemplateURL`. If both are
            passed, only `TemplateBody` is used.

        :type template_url: string
        :param template_url: Location of file containing the template body. The
            URL must point to a template (max size: 307,200 bytes) located in
            an S3 bucket in the same region as the stack. For more information,
            go to the `Template Anatomy`_ in the AWS CloudFormation User Guide.
        Conditional: You must pass `TemplateURL` or `TemplateBody`. If both are
            passed, only `TemplateBody` is used.

        :type parameters: list
        :param parameters: A list of `Parameter` structures that specify input
            parameters for the stack.

        :type disable_rollback: boolean
        :param disable_rollback: Set to `True` to disable rollback of the stack
            if stack creation failed. You can specify either `DisableRollback`
            or `OnFailure`, but not both.
        Default: `False`

        :type timeout_in_minutes: integer
        :param timeout_in_minutes: The amount of time that can pass before the
            stack status becomes CREATE_FAILED; if `DisableRollback` is not set
            or is set to `False`, the stack will be rolled back.

        :type notification_arns: list
        :param notification_arns: The Simple Notification Service (SNS) topic
            ARNs to publish stack related events. You can find your SNS topic
            ARNs using the `SNS console`_ or your Command Line Interface (CLI).

        :type capabilities: list
        :param capabilities: The list of capabilities that you want to allow in
            the stack. If your template contains certain resources, you must
            specify the CAPABILITY_IAM value for this parameter; otherwise,
            this action returns an InsufficientCapabilities error. The
            following resources require you to specify the capabilities
            parameter: `AWS::CloudFormation::Stack`_, `AWS::IAM::AccessKey`_,
            `AWS::IAM::Group`_, `AWS::IAM::InstanceProfile`_,
            `AWS::IAM::Policy`_, `AWS::IAM::Role`_, `AWS::IAM::User`_, and
            `AWS::IAM::UserToGroupAddition`_.

        :type on_failure: string
        :param on_failure: Determines what action will be taken if stack
            creation fails. This must be one of: DO_NOTHING, ROLLBACK, or
            DELETE. You can specify either `OnFailure` or `DisableRollback`,
            but not both.
        Default: `ROLLBACK`

        :type stack_policy_body: string
        :param stack_policy_body: Structure containing the stack policy body.
            (For more information, go to ` Prevent Updates to Stack Resources`_
            in the AWS CloudFormation User Guide.)
        If you pass `StackPolicyBody` and `StackPolicyURL`, only
            `StackPolicyBody` is used.

        :type stack_policy_url: string
        :param stack_policy_url: Location of a file containing the stack
            policy. The URL must point to a policy (max size: 16KB) located in
            an S3 bucket in the same region as the stack. If you pass
            `StackPolicyBody` and `StackPolicyURL`, only `StackPolicyBody` is
            used.

        :type tags: list
        :param tags: A set of user-defined `Tags` to associate with this stack,
            represented by key/value pairs. Tags defined for the stack are
            propagated to EC2 resources that are created as part of the stack.
            A maximum number of 10 tags can be specified.

        """
        params = {'StackName': stack_name, }
        if template_body is not None:
            params['TemplateBody'] = template_body
        if template_url is not None:
            params['TemplateURL'] = template_url
        if parameters is not None:
            self.build_complex_list_params(
                params, parameters,
                'Parameters.member',
                ('ParameterKey', 'ParameterValue'))
        if disable_rollback is not None:
            params['DisableRollback'] = str(
                disable_rollback).lower()
        if timeout_in_minutes is not None:
            params['TimeoutInMinutes'] = timeout_in_minutes
        if notification_arns is not None:
            self.build_list_params(params,
                                   notification_arns,
                                   'NotificationARNs.member')
        if capabilities is not None:
            self.build_list_params(params,
                                   capabilities,
                                   'Capabilities.member')
        if on_failure is not None:
            params['OnFailure'] = on_failure
        if stack_policy_body is not None:
            params['StackPolicyBody'] = stack_policy_body
        if stack_policy_url is not None:
            params['StackPolicyURL'] = stack_policy_url
        if tags is not None:
            self.build_complex_list_params(
                params, tags,
                'Tags.member',
                ('Key', 'Value'))
        return self._make_request(
            action='CreateStack',
            verb='POST',
            path='/', params=params)

    def delete_stack(self, stack_name):
        """
        Deletes a specified stack. Once the call completes
        successfully, stack deletion starts. Deleted stacks do not
        show up in the DescribeStacks API if the deletion has been
        completed successfully.

        :type stack_name: string
        :param stack_name: The name or the unique identifier associated with
            the stack.

        """
        params = {'StackName': stack_name, }
        return self._make_request(
            action='DeleteStack',
            verb='POST',
            path='/', params=params)

    def describe_stack_events(self, stack_name=None, next_token=None):
        """
        Returns all stack related events for a specified stack. For
        more information about a stack's event history, go to
        `Stacks`_ in the AWS CloudFormation User Guide.
        Events are returned, even if the stack never existed or has
        been successfully deleted.

        :type stack_name: string
        :param stack_name: The name or the unique identifier associated with
            the stack.
        Default: There is no default value.

        :type next_token: string
        :param next_token: String that identifies the start of the next list of
            events, if there is one.
        Default: There is no default value.

        """
        params = {}
        if stack_name is not None:
            params['StackName'] = stack_name
        if next_token is not None:
            params['NextToken'] = next_token
        return self._make_request(
            action='DescribeStackEvents',
            verb='POST',
            path='/', params=params)

    def describe_stack_resource(self, stack_name, logical_resource_id):
        """
        Returns a description of the specified resource in the
        specified stack.

        For deleted stacks, DescribeStackResource returns resource
        information for up to 90 days after the stack has been
        deleted.

        :type stack_name: string
        :param stack_name: The name or the unique identifier associated with
            the stack.
        Default: There is no default value.

        :type logical_resource_id: string
        :param logical_resource_id: The logical name of the resource as
            specified in the template.
        Default: There is no default value.

        """
        params = {
            'StackName': stack_name,
            'LogicalResourceId': logical_resource_id,
        }
        return self._make_request(
            action='DescribeStackResource',
            verb='POST',
            path='/', params=params)

    def describe_stack_resources(self, stack_name=None,
                                 logical_resource_id=None,
                                 physical_resource_id=None):
        """
        Returns AWS resource descriptions for running and deleted
        stacks. If `StackName` is specified, all the associated
        resources that are part of the stack are returned. If
        `PhysicalResourceId` is specified, the associated resources of
        the stack that the resource belongs to are returned.
        Only the first 100 resources will be returned. If your stack
        has more resources than this, you should use
        `ListStackResources` instead.
        For deleted stacks, `DescribeStackResources` returns resource
        information for up to 90 days after the stack has been
        deleted.

        You must specify either `StackName` or `PhysicalResourceId`,
        but not both. In addition, you can specify `LogicalResourceId`
        to filter the returned result. For more information about
        resources, the `LogicalResourceId` and `PhysicalResourceId`,
        go to the `AWS CloudFormation User Guide`_.
        A `ValidationError` is returned if you specify both
        `StackName` and `PhysicalResourceId` in the same request.

        :type stack_name: string
        :param stack_name: The name or the unique identifier associated with
            the stack.
        Required: Conditional. If you do not specify `StackName`, you must
            specify `PhysicalResourceId`.

        Default: There is no default value.

        :type logical_resource_id: string
        :param logical_resource_id: The logical name of the resource as
            specified in the template.
        Default: There is no default value.

        :type physical_resource_id: string
        :param physical_resource_id: The name or unique identifier that
            corresponds to a physical instance ID of a resource supported by
            AWS CloudFormation.
        For example, for an Amazon Elastic Compute Cloud (EC2) instance,
            `PhysicalResourceId` corresponds to the `InstanceId`. You can pass
            the EC2 `InstanceId` to `DescribeStackResources` to find which
            stack the instance belongs to and what other resources are part of
            the stack.

        Required: Conditional. If you do not specify `PhysicalResourceId`, you
            must specify `StackName`.

        Default: There is no default value.

        """
        params = {}
        if stack_name is not None:
            params['StackName'] = stack_name
        if logical_resource_id is not None:
            params['LogicalResourceId'] = logical_resource_id
        if physical_resource_id is not None:
            params['PhysicalResourceId'] = physical_resource_id
        return self._make_request(
            action='DescribeStackResources',
            verb='POST',
            path='/', params=params)

    def describe_stacks(self, stack_name=None, next_token=None):
        """
        Returns the description for the specified stack; if no stack
        name was specified, then it returns the description for all
        the stacks created.

        :type stack_name: string
        :param stack_name: The name or the unique identifier associated with
            the stack.
        Default: There is no default value.

        :type next_token: string
        :param next_token: String that identifies the start of the next list of
            stacks, if there is one.

        """
        params = {}
        if stack_name is not None:
            params['StackName'] = stack_name
        if next_token is not None:
            params['NextToken'] = next_token
        return self._make_request(
            action='DescribeStacks',
            verb='POST',
            path='/', params=params)

    def estimate_template_cost(self, template_body=None, template_url=None,
                               parameters=None):
        """
        Returns the estimated monthly cost of a template. The return
        value is an AWS Simple Monthly Calculator URL with a query
        string that describes the resources required to run the
        template.

        :type template_body: string
        :param template_body: Structure containing the template body. (For more
            information, go to `Template Anatomy`_ in the AWS CloudFormation
            User Guide.)
        Conditional: You must pass `TemplateBody` or `TemplateURL`. If both are
            passed, only `TemplateBody` is used.

        :type template_url: string
        :param template_url: Location of file containing the template body. The
            URL must point to a template located in an S3 bucket in the same
            region as the stack. For more information, go to `Template
            Anatomy`_ in the AWS CloudFormation User Guide.
        Conditional: You must pass `TemplateURL` or `TemplateBody`. If both are
            passed, only `TemplateBody` is used.

        :type parameters: list
        :param parameters: A list of `Parameter` structures that specify input
            parameters.

        """
        params = {}
        if template_body is not None:
            params['TemplateBody'] = template_body
        if template_url is not None:
            params['TemplateURL'] = template_url
        if parameters is not None:
            self.build_complex_list_params(
                params, parameters,
                'Parameters.member',
                ('ParameterKey', 'ParameterValue'))
        return self._make_request(
            action='EstimateTemplateCost',
            verb='POST',
            path='/', params=params)

    def get_stack_policy(self, stack_name):
        """
        Returns the stack policy for a specified stack. If a stack
        doesn't have a policy, a null value is returned.

        :type stack_name: string
        :param stack_name: The name or stack ID that is associated with the
            stack whose policy you want to get.

        """
        params = {'StackName': stack_name, }
        return self._make_request(
            action='GetStackPolicy',
            verb='POST',
            path='/', params=params)

    def get_template(self, stack_name):
        """
        Returns the template body for a specified stack. You can get
        the template for running or deleted stacks.

        For deleted stacks, GetTemplate returns the template for up to
        90 days after the stack has been deleted.
        If the template does not exist, a `ValidationError` is
        returned.

        :type stack_name: string
        :param stack_name: The name or the unique identifier associated with
            the stack, which are not always interchangeable:

        + Running stacks: You can specify either the stack's name or its unique
              stack ID.
        + Deleted stacks: You must specify the unique stack ID.


        Default: There is no default value.

        """
        params = {'StackName': stack_name, }
        return self._make_request(
            action='GetTemplate',
            verb='POST',
            path='/', params=params)

    def list_stack_resources(self, stack_name, next_token=None):
        """
        Returns descriptions of all resources of the specified stack.

        For deleted stacks, ListStackResources returns resource
        information for up to 90 days after the stack has been
        deleted.

        :type stack_name: string
        :param stack_name: The name or the unique identifier associated with
            the stack, which are not always interchangeable:

        + Running stacks: You can specify either the stack's name or its unique
              stack ID.
        + Deleted stacks: You must specify the unique stack ID.


        Default: There is no default value.

        :type next_token: string
        :param next_token: String that identifies the start of the next list of
            stack resource summaries, if there is one.
        Default: There is no default value.

        """
        params = {'StackName': stack_name, }
        if next_token is not None:
            params['NextToken'] = next_token
        return self._make_request(
            action='ListStackResources',
            verb='POST',
            path='/', params=params)

    def list_stacks(self, next_token=None, stack_status_filter=None):
        """
        Returns the summary information for stacks whose status
        matches the specified StackStatusFilter. Summary information
        for stacks that have been deleted is kept for 90 days after
        the stack is deleted. If no StackStatusFilter is specified,
        summary information for all stacks is returned (including
        existing stacks and stacks that have been deleted).

        :type next_token: string
        :param next_token: String that identifies the start of the next list of
            stacks, if there is one.
        Default: There is no default value.

        :type stack_status_filter: list
        :param stack_status_filter: Stack status to use as a filter. Specify
            one or more stack status codes to list only stacks with the
            specified status codes. For a complete list of stack status codes,
            see the `StackStatus` parameter of the Stack data type.

        """
        params = {}
        if next_token is not None:
            params['NextToken'] = next_token
        if stack_status_filter is not None:
            self.build_list_params(params,
                                   stack_status_filter,
                                   'StackStatusFilter.member')
        return self._make_request(
            action='ListStacks',
            verb='POST',
            path='/', params=params)

    def set_stack_policy(self, stack_name, stack_policy_body=None,
                         stack_policy_url=None):
        """
        Sets a stack policy for a specified stack.

        :type stack_name: string
        :param stack_name: The name or stack ID that you want to associate a
            policy with.

        :type stack_policy_body: string
        :param stack_policy_body: Structure containing the stack policy body.
            (For more information, go to ` Prevent Updates to Stack Resources`_
            in the AWS CloudFormation User Guide.)
        You must pass `StackPolicyBody` or `StackPolicyURL`. If both are
            passed, only `StackPolicyBody` is used.

        :type stack_policy_url: string
        :param stack_policy_url: Location of a file containing the stack
            policy. The URL must point to a policy (max size: 16KB) located in
            an S3 bucket in the same region as the stack. You must pass
            `StackPolicyBody` or `StackPolicyURL`. If both are passed, only
            `StackPolicyBody` is used.

        """
        params = {'StackName': stack_name, }
        if stack_policy_body is not None:
            params['StackPolicyBody'] = stack_policy_body
        if stack_policy_url is not None:
            params['StackPolicyURL'] = stack_policy_url
        return self._make_request(
            action='SetStackPolicy',
            verb='POST',
            path='/', params=params)

    def update_stack(self, stack_name, template_body=None, template_url=None,
                     stack_policy_during_update_body=None,
                     stack_policy_during_update_url=None, parameters=None,
                     capabilities=None, stack_policy_body=None,
                     stack_policy_url=None):
        """
        Updates a stack as specified in the template. After the call
        completes successfully, the stack update starts. You can check
        the status of the stack via the DescribeStacks action.



        **Note: **You cannot update `AWS::S3::Bucket`_ resources, for
        example, to add or modify tags.



        To get a copy of the template for an existing stack, you can
        use the GetTemplate action.

        Tags that were associated with this stack during creation time
        will still be associated with the stack after an `UpdateStack`
        operation.

        For more information about creating an update template,
        updating a stack, and monitoring the progress of the update,
        see `Updating a Stack`_.

        :type stack_name: string
        :param stack_name:
        The name or stack ID of the stack to update.

        Must contain only alphanumeric characters (case sensitive) and start
            with an alpha character. Maximum length of the name is 255
            characters.

        :type template_body: string
        :param template_body: Structure containing the template body. (For more
            information, go to `Template Anatomy`_ in the AWS CloudFormation
            User Guide.)
        Conditional: You must pass `TemplateBody` or `TemplateURL`. If both are
            passed, only `TemplateBody` is used.

        :type template_url: string
        :param template_url: Location of file containing the template body. The
            URL must point to a template located in an S3 bucket in the same
            region as the stack. For more information, go to `Template
            Anatomy`_ in the AWS CloudFormation User Guide.
        Conditional: You must pass `TemplateURL` or `TemplateBody`. If both are
            passed, only `TemplateBody` is used.

        :type stack_policy_during_update_body: string
        :param stack_policy_during_update_body: Structure containing the
            temporary overriding stack policy body. If you pass
            `StackPolicyDuringUpdateBody` and `StackPolicyDuringUpdateURL`,
            only `StackPolicyDuringUpdateBody` is used.
        If you want to update protected resources, specify a temporary
            overriding stack policy during this update. If you do not specify a
            stack policy, the current policy that associated with the stack
            will be used.

        :type stack_policy_during_update_url: string
        :param stack_policy_during_update_url: Location of a file containing
            the temporary overriding stack policy. The URL must point to a
            policy (max size: 16KB) located in an S3 bucket in the same region
            as the stack. If you pass `StackPolicyDuringUpdateBody` and
            `StackPolicyDuringUpdateURL`, only `StackPolicyDuringUpdateBody` is
            used.
        If you want to update protected resources, specify a temporary
            overriding stack policy during this update. If you do not specify a
            stack policy, the current policy that is associated with the stack
            will be used.

        :type parameters: list
        :param parameters: A list of `Parameter` structures that specify input
            parameters for the stack.

        :type capabilities: list
        :param capabilities: The list of capabilities that you want to allow in
            the stack. If your stack contains IAM resources, you must specify
            the CAPABILITY_IAM value for this parameter; otherwise, this action
            returns an InsufficientCapabilities error. IAM resources are the
            following: `AWS::IAM::AccessKey`_, `AWS::IAM::Group`_,
            `AWS::IAM::Policy`_, `AWS::IAM::User`_, and
            `AWS::IAM::UserToGroupAddition`_.

        :type stack_policy_body: string
        :param stack_policy_body: Structure containing the updated stack policy
            body. If you pass `StackPolicyBody` and `StackPolicyURL`, only
            `StackPolicyBody` is used.
        If you want to update a stack policy during a stack update, specify an
            updated stack policy. For example, you can include an updated stack
            policy to protect a new resource created in the stack update. If
            you do not specify a stack policy, the current policy that is
            associated with the stack is unchanged.

        :type stack_policy_url: string
        :param stack_policy_url: Location of a file containing the updated
            stack policy. The URL must point to a policy (max size: 16KB)
            located in an S3 bucket in the same region as the stack. If you
            pass `StackPolicyBody` and `StackPolicyURL`, only `StackPolicyBody`
            is used.
        If you want to update a stack policy during a stack update, specify an
            updated stack policy. For example, you can include an updated stack
            policy to protect a new resource created in the stack update. If
            you do not specify a stack policy, the current policy that is
            associated with the stack is unchanged.

        """
        params = {'StackName': stack_name, }
        if template_body is not None:
            params['TemplateBody'] = template_body
        if template_url is not None:
            params['TemplateURL'] = template_url
        if stack_policy_during_update_body is not None:
            params['StackPolicyDuringUpdateBody'] = stack_policy_during_update_body
        if stack_policy_during_update_url is not None:
            params['StackPolicyDuringUpdateURL'] = stack_policy_during_update_url
        if parameters is not None:
            self.build_complex_list_params(
                params, parameters,
                'Parameters.member',
                ('ParameterKey', 'ParameterValue'))
        if capabilities is not None:
            self.build_list_params(params,
                                   capabilities,
                                   'Capabilities.member')
        if stack_policy_body is not None:
            params['StackPolicyBody'] = stack_policy_body
        if stack_policy_url is not None:
            params['StackPolicyURL'] = stack_policy_url
        return self._make_request(
            action='UpdateStack',
            verb='POST',
            path='/', params=params)

    def validate_template(self, template_body=None, template_url=None):
        """
        Validates a specified template.

        :type template_body: string
        :param template_body: String containing the template body. (For more
            information, go to `Template Anatomy`_ in the AWS CloudFormation
            User Guide.)
        Conditional: You must pass `TemplateURL` or `TemplateBody`. If both are
            passed, only `TemplateBody` is used.

        :type template_url: string
        :param template_url: Location of file containing the template body. The
            URL must point to a template (max size: 307,200 bytes) located in
            an S3 bucket in the same region as the stack. For more information,
            go to `Template Anatomy`_ in the AWS CloudFormation User Guide.
        Conditional: You must pass `TemplateURL` or `TemplateBody`. If both are
            passed, only `TemplateBody` is used.

        """
        params = {}
        if template_body is not None:
            params['TemplateBody'] = template_body
        if template_url is not None:
            params['TemplateURL'] = template_url
        return self._make_request(
            action='ValidateTemplate',
            verb='POST',
            path='/', params=params)

    def _make_request(self, action, verb, path, params):
        params['ContentType'] = 'JSON'
        response = self.make_request(action=action, verb='POST',
                                     path='/', params=params)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            return json.loads(body)
        else:
            json_body = json.loads(body)
            fault_name = json_body.get('Error', {}).get('Code', None)
            exception_class = self._faults.get(fault_name, self.ResponseError)
            raise exception_class(response.status, response.reason,
                                  body=json_body)
