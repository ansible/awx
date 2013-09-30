# Copyright (c) 2010-2011 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010-2011, Eucalyptus Systems, Inc.
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
import boto
import boto.jsonresponse
from boto.compat import json
from boto.resultset import ResultSet
from boto.iam.summarymap import SummaryMap
from boto.connection import AWSQueryConnection


ASSUME_ROLE_POLICY_DOCUMENT = json.dumps({
    'Statement': [{'Principal': {'Service': ['ec2.amazonaws.com']},
                   'Effect': 'Allow',
                   'Action': ['sts:AssumeRole']}]})


class IAMConnection(AWSQueryConnection):

    APIVersion = '2010-05-08'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, host='iam.amazonaws.com',
                 debug=0, https_connection_factory=None,
                 path='/', security_token=None, validate_certs=True):
        AWSQueryConnection.__init__(self, aws_access_key_id,
                                    aws_secret_access_key,
                                    is_secure, port, proxy,
                                    proxy_port, proxy_user, proxy_pass,
                                    host, debug, https_connection_factory,
                                    path, security_token,
                                    validate_certs=validate_certs)

    def _required_auth_capability(self):
        #return ['iam']
        return ['hmac-v4']

    def get_response(self, action, params, path='/', parent=None,
                     verb='POST', list_marker='Set'):
        """
        Utility method to handle calls to IAM and parsing of responses.
        """
        if not parent:
            parent = self
        response = self.make_request(action, params, path, verb)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            e = boto.jsonresponse.Element(list_marker=list_marker,
                                          pythonize_name=True)
            h = boto.jsonresponse.XmlHandler(e, parent)
            h.parse(body)
            return e
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)

    #
    # Group methods
    #

    def get_all_groups(self, path_prefix='/', marker=None, max_items=None):
        """
        List the groups that have the specified path prefix.

        :type path_prefix: string
        :param path_prefix: If provided, only groups whose paths match
            the provided prefix will be returned.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {}
        if path_prefix:
            params['PathPrefix'] = path_prefix
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListGroups', params,
                                 list_marker='Groups')

    def get_group(self, group_name, marker=None, max_items=None):
        """
        Return a list of users that are in the specified group.

        :type group_name: string
        :param group_name: The name of the group whose information should
                           be returned.
        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'GroupName': group_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('GetGroup', params, list_marker='Users')

    def create_group(self, group_name, path='/'):
        """
        Create a group.

        :type group_name: string
        :param group_name: The name of the new group

        :type path: string
        :param path: The path to the group (Optional).  Defaults to /.

        """
        params = {'GroupName': group_name,
                  'Path': path}
        return self.get_response('CreateGroup', params)

    def delete_group(self, group_name):
        """
        Delete a group. The group must not contain any Users or
        have any attached policies

        :type group_name: string
        :param group_name: The name of the group to delete.

        """
        params = {'GroupName': group_name}
        return self.get_response('DeleteGroup', params)

    def update_group(self, group_name, new_group_name=None, new_path=None):
        """
        Updates name and/or path of the specified group.

        :type group_name: string
        :param group_name: The name of the new group

        :type new_group_name: string
        :param new_group_name: If provided, the name of the group will be
            changed to this name.

        :type new_path: string
        :param new_path: If provided, the path of the group will be
            changed to this path.

        """
        params = {'GroupName': group_name}
        if new_group_name:
            params['NewGroupName'] = new_group_name
        if new_path:
            params['NewPath'] = new_path
        return self.get_response('UpdateGroup', params)

    def add_user_to_group(self, group_name, user_name):
        """
        Add a user to a group

        :type group_name: string
        :param group_name: The name of the group

        :type user_name: string
        :param user_name: The to be added to the group.

        """
        params = {'GroupName': group_name,
                  'UserName': user_name}
        return self.get_response('AddUserToGroup', params)

    def remove_user_from_group(self, group_name, user_name):
        """
        Remove a user from a group.

        :type group_name: string
        :param group_name: The name of the group

        :type user_name: string
        :param user_name: The user to remove from the group.

        """
        params = {'GroupName': group_name,
                  'UserName': user_name}
        return self.get_response('RemoveUserFromGroup', params)

    def put_group_policy(self, group_name, policy_name, policy_json):
        """
        Adds or updates the specified policy document for the specified group.

        :type group_name: string
        :param group_name: The name of the group the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to get.

        :type policy_json: string
        :param policy_json: The policy document.

        """
        params = {'GroupName': group_name,
                  'PolicyName': policy_name,
                  'PolicyDocument': policy_json}
        return self.get_response('PutGroupPolicy', params, verb='POST')

    def get_all_group_policies(self, group_name, marker=None, max_items=None):
        """
        List the names of the policies associated with the specified group.

        :type group_name: string
        :param group_name: The name of the group the policy is associated with.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'GroupName': group_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListGroupPolicies', params,
                                 list_marker='PolicyNames')

    def get_group_policy(self, group_name, policy_name):
        """
        Retrieves the specified policy document for the specified group.

        :type group_name: string
        :param group_name: The name of the group the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to get.

        """
        params = {'GroupName': group_name,
                  'PolicyName': policy_name}
        return self.get_response('GetGroupPolicy', params, verb='POST')

    def delete_group_policy(self, group_name, policy_name):
        """
        Deletes the specified policy document for the specified group.

        :type group_name: string
        :param group_name: The name of the group the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to delete.

        """
        params = {'GroupName': group_name,
                  'PolicyName': policy_name}
        return self.get_response('DeleteGroupPolicy', params, verb='POST')

    def get_all_users(self, path_prefix='/', marker=None, max_items=None):
        """
        List the users that have the specified path prefix.

        :type path_prefix: string
        :param path_prefix: If provided, only users whose paths match
            the provided prefix will be returned.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'PathPrefix': path_prefix}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListUsers', params, list_marker='Users')

    #
    # User methods
    #

    def create_user(self, user_name, path='/'):
        """
        Create a user.

        :type user_name: string
        :param user_name: The name of the new user

        :type path: string
        :param path: The path in which the user will be created.
            Defaults to /.

        """
        params = {'UserName': user_name,
                  'Path': path}
        return self.get_response('CreateUser', params)

    def delete_user(self, user_name):
        """
        Delete a user including the user's path, GUID and ARN.

        If the user_name is not specified, the user_name is determined
        implicitly based on the AWS Access Key ID used to sign the request.

        :type user_name: string
        :param user_name: The name of the user to delete.

        """
        params = {'UserName': user_name}
        return self.get_response('DeleteUser', params)

    def get_user(self, user_name=None):
        """
        Retrieve information about the specified user.

        If the user_name is not specified, the user_name is determined
        implicitly based on the AWS Access Key ID used to sign the request.

        :type user_name: string
        :param user_name: The name of the user to retrieve.
            If not specified, defaults to user making request.
        """
        params = {}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('GetUser', params)

    def update_user(self, user_name, new_user_name=None, new_path=None):
        """
        Updates name and/or path of the specified user.

        :type user_name: string
        :param user_name: The name of the user

        :type new_user_name: string
        :param new_user_name: If provided, the username of the user will be
            changed to this username.

        :type new_path: string
        :param new_path: If provided, the path of the user will be
            changed to this path.

        """
        params = {'UserName': user_name}
        if new_user_name:
            params['NewUserName'] = new_user_name
        if new_path:
            params['NewPath'] = new_path
        return self.get_response('UpdateUser', params)

    def get_all_user_policies(self, user_name, marker=None, max_items=None):
        """
        List the names of the policies associated with the specified user.

        :type user_name: string
        :param user_name: The name of the user the policy is associated with.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'UserName': user_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListUserPolicies', params,
                                 list_marker='PolicyNames')

    def put_user_policy(self, user_name, policy_name, policy_json):
        """
        Adds or updates the specified policy document for the specified user.

        :type user_name: string
        :param user_name: The name of the user the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to get.

        :type policy_json: string
        :param policy_json: The policy document.

        """
        params = {'UserName': user_name,
                  'PolicyName': policy_name,
                  'PolicyDocument': policy_json}
        return self.get_response('PutUserPolicy', params, verb='POST')

    def get_user_policy(self, user_name, policy_name):
        """
        Retrieves the specified policy document for the specified user.

        :type user_name: string
        :param user_name: The name of the user the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to get.

        """
        params = {'UserName': user_name,
                  'PolicyName': policy_name}
        return self.get_response('GetUserPolicy', params, verb='POST')

    def delete_user_policy(self, user_name, policy_name):
        """
        Deletes the specified policy document for the specified user.

        :type user_name: string
        :param user_name: The name of the user the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to delete.

        """
        params = {'UserName': user_name,
                  'PolicyName': policy_name}
        return self.get_response('DeleteUserPolicy', params, verb='POST')

    def get_groups_for_user(self, user_name, marker=None, max_items=None):
        """
        List the groups that a specified user belongs to.

        :type user_name: string
        :param user_name: The name of the user to list groups for.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'UserName': user_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListGroupsForUser', params,
                                 list_marker='Groups')

    #
    # Access Keys
    #

    def get_all_access_keys(self, user_name, marker=None, max_items=None):
        """
        Get all access keys associated with an account.

        :type user_name: string
        :param user_name: The username of the user

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'UserName': user_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListAccessKeys', params,
                                 list_marker='AccessKeyMetadata')

    def create_access_key(self, user_name=None):
        """
        Create a new AWS Secret Access Key and corresponding AWS Access Key ID
        for the specified user.  The default status for new keys is Active

        If the user_name is not specified, the user_name is determined
        implicitly based on the AWS Access Key ID used to sign the request.

        :type user_name: string
        :param user_name: The username of the user

        """
        params = {'UserName': user_name}
        return self.get_response('CreateAccessKey', params)

    def update_access_key(self, access_key_id, status, user_name=None):
        """
        Changes the status of the specified access key from Active to Inactive
        or vice versa.  This action can be used to disable a user's key as
        part of a key rotation workflow.

        If the user_name is not specified, the user_name is determined
        implicitly based on the AWS Access Key ID used to sign the request.

        :type access_key_id: string
        :param access_key_id: The ID of the access key.

        :type status: string
        :param status: Either Active or Inactive.

        :type user_name: string
        :param user_name: The username of user (optional).

        """
        params = {'AccessKeyId': access_key_id,
                  'Status': status}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('UpdateAccessKey', params)

    def delete_access_key(self, access_key_id, user_name=None):
        """
        Delete an access key associated with a user.

        If the user_name is not specified, it is determined implicitly based
        on the AWS Access Key ID used to sign the request.

        :type access_key_id: string
        :param access_key_id: The ID of the access key to be deleted.

        :type user_name: string
        :param user_name: The username of the user

        """
        params = {'AccessKeyId': access_key_id}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('DeleteAccessKey', params)

    #
    # Signing Certificates
    #

    def get_all_signing_certs(self, marker=None, max_items=None,
                              user_name=None):
        """
        Get all signing certificates associated with an account.

        If the user_name is not specified, it is determined implicitly based
        on the AWS Access Key ID used to sign the request.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.

        :type user_name: string
        :param user_name: The username of the user

        """
        params = {}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        if user_name:
            params['UserName'] = user_name
        return self.get_response('ListSigningCertificates',
                                 params, list_marker='Certificates')

    def update_signing_cert(self, cert_id, status, user_name=None):
        """
        Change the status of the specified signing certificate from
        Active to Inactive or vice versa.

        If the user_name is not specified, it is determined implicitly based
        on the AWS Access Key ID used to sign the request.

        :type cert_id: string
        :param cert_id: The ID of the signing certificate

        :type status: string
        :param status: Either Active or Inactive.

        :type user_name: string
        :param user_name: The username of the user
        """
        params = {'CertificateId': cert_id,
                  'Status': status}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('UpdateSigningCertificate', params)

    def upload_signing_cert(self, cert_body, user_name=None):
        """
        Uploads an X.509 signing certificate and associates it with
        the specified user.

        If the user_name is not specified, it is determined implicitly based
        on the AWS Access Key ID used to sign the request.

        :type cert_body: string
        :param cert_body: The body of the signing certificate.

        :type user_name: string
        :param user_name: The username of the user

        """
        params = {'CertificateBody': cert_body}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('UploadSigningCertificate', params,
                                 verb='POST')

    def delete_signing_cert(self, cert_id, user_name=None):
        """
        Delete a signing certificate associated with a user.

        If the user_name is not specified, it is determined implicitly based
        on the AWS Access Key ID used to sign the request.

        :type user_name: string
        :param user_name: The username of the user

        :type cert_id: string
        :param cert_id: The ID of the certificate.

        """
        params = {'CertificateId': cert_id}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('DeleteSigningCertificate', params)

    #
    # Server Certificates
    #

    def list_server_certs(self, path_prefix='/',
                             marker=None, max_items=None):
        """
        Lists the server certificates that have the specified path prefix.
        If none exist, the action returns an empty list.

        :type path_prefix: string
        :param path_prefix: If provided, only certificates whose paths match
            the provided prefix will be returned.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.

        """
        params = {}
        if path_prefix:
            params['PathPrefix'] = path_prefix
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListServerCertificates',
                                 params,
                                 list_marker='ServerCertificateMetadataList')

    # Preserves backwards compatibility.
    # TODO: Look into deprecating this eventually?
    get_all_server_certs = list_server_certs

    def update_server_cert(self, cert_name, new_cert_name=None,
                           new_path=None):
        """
        Updates the name and/or the path of the specified server certificate.

        :type cert_name: string
        :param cert_name: The name of the server certificate that you want
            to update.

        :type new_cert_name: string
        :param new_cert_name: The new name for the server certificate.
            Include this only if you are updating the
            server certificate's name.

        :type new_path: string
        :param new_path: If provided, the path of the certificate will be
                         changed to this path.
        """
        params = {'ServerCertificateName': cert_name}
        if new_cert_name:
            params['NewServerCertificateName'] = new_cert_name
        if new_path:
            params['NewPath'] = new_path
        return self.get_response('UpdateServerCertificate', params)

    def upload_server_cert(self, cert_name, cert_body, private_key,
                           cert_chain=None, path=None):
        """
        Uploads a server certificate entity for the AWS Account.
        The server certificate entity includes a public key certificate,
        a private key, and an optional certificate chain, which should
        all be PEM-encoded.

        :type cert_name: string
        :param cert_name: The name for the server certificate. Do not
            include the path in this value.

        :type cert_body: string
        :param cert_body: The contents of the public key certificate
            in PEM-encoded format.

        :type private_key: string
        :param private_key: The contents of the private key in
            PEM-encoded format.

        :type cert_chain: string
        :param cert_chain: The contents of the certificate chain. This
            is typically a concatenation of the PEM-encoded
            public key certificates of the chain.

        :type path: string
        :param path: The path for the server certificate.
        """
        params = {'ServerCertificateName': cert_name,
                  'CertificateBody': cert_body,
                  'PrivateKey': private_key}
        if cert_chain:
            params['CertificateChain'] = cert_chain
        if path:
            params['Path'] = path
        return self.get_response('UploadServerCertificate', params,
                                 verb='POST')

    def get_server_certificate(self, cert_name):
        """
        Retrieves information about the specified server certificate.

        :type cert_name: string
        :param cert_name: The name of the server certificate you want
            to retrieve information about.

        """
        params = {'ServerCertificateName': cert_name}
        return self.get_response('GetServerCertificate', params)

    def delete_server_cert(self, cert_name):
        """
        Delete the specified server certificate.

        :type cert_name: string
        :param cert_name: The name of the server certificate you want
            to delete.

        """
        params = {'ServerCertificateName': cert_name}
        return self.get_response('DeleteServerCertificate', params)

    #
    # MFA Devices
    #

    def get_all_mfa_devices(self, user_name, marker=None, max_items=None):
        """
        Get all MFA devices associated with an account.

        :type user_name: string
        :param user_name: The username of the user

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.

        """
        params = {'UserName': user_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListMFADevices',
                                 params, list_marker='MFADevices')

    def enable_mfa_device(self, user_name, serial_number,
                          auth_code_1, auth_code_2):
        """
        Enables the specified MFA device and associates it with the
        specified user.

        :type user_name: string
        :param user_name: The username of the user

        :type serial_number: string
        :param seriasl_number: The serial number which uniquely identifies
            the MFA device.

        :type auth_code_1: string
        :param auth_code_1: An authentication code emitted by the device.

        :type auth_code_2: string
        :param auth_code_2: A subsequent authentication code emitted
            by the device.

        """
        params = {'UserName': user_name,
                  'SerialNumber': serial_number,
                  'AuthenticationCode1': auth_code_1,
                  'AuthenticationCode2': auth_code_2}
        return self.get_response('EnableMFADevice', params)

    def deactivate_mfa_device(self, user_name, serial_number):
        """
        Deactivates the specified MFA device and removes it from
        association with the user.

        :type user_name: string
        :param user_name: The username of the user

        :type serial_number: string
        :param seriasl_number: The serial number which uniquely identifies
            the MFA device.

        """
        params = {'UserName': user_name,
                  'SerialNumber': serial_number}
        return self.get_response('DeactivateMFADevice', params)

    def resync_mfa_device(self, user_name, serial_number,
                          auth_code_1, auth_code_2):
        """
        Syncronizes the specified MFA device with the AWS servers.

        :type user_name: string
        :param user_name: The username of the user

        :type serial_number: string
        :param seriasl_number: The serial number which uniquely identifies
            the MFA device.

        :type auth_code_1: string
        :param auth_code_1: An authentication code emitted by the device.

        :type auth_code_2: string
        :param auth_code_2: A subsequent authentication code emitted
            by the device.

        """
        params = {'UserName': user_name,
                  'SerialNumber': serial_number,
                  'AuthenticationCode1': auth_code_1,
                  'AuthenticationCode2': auth_code_2}
        return self.get_response('ResyncMFADevice', params)

    #
    # Login Profiles
    #

    def get_login_profiles(self, user_name):
        """
        Retrieves the login profile for the specified user.

        :type user_name: string
        :param user_name: The username of the user

        """
        params = {'UserName': user_name}
        return self.get_response('GetLoginProfile', params)

    def create_login_profile(self, user_name, password):
        """
        Creates a login profile for the specified user, give the user the
        ability to access AWS services and the AWS Management Console.

        :type user_name: string
        :param user_name: The name of the user

        :type password: string
        :param password: The new password for the user

        """
        params = {'UserName': user_name,
                  'Password': password}
        return self.get_response('CreateLoginProfile', params)

    def delete_login_profile(self, user_name):
        """
        Deletes the login profile associated with the specified user.

        :type user_name: string
        :param user_name: The name of the user to delete.

        """
        params = {'UserName': user_name}
        return self.get_response('DeleteLoginProfile', params)

    def update_login_profile(self, user_name, password):
        """
        Resets the password associated with the user's login profile.

        :type user_name: string
        :param user_name: The name of the user

        :type password: string
        :param password: The new password for the user

        """
        params = {'UserName': user_name,
                  'Password': password}
        return self.get_response('UpdateLoginProfile', params)

    def create_account_alias(self, alias):
        """
        Creates a new alias for the AWS account.

        For more information on account id aliases, please see
        http://goo.gl/ToB7G

        :type alias: string
        :param alias: The alias to attach to the account.
        """
        params = {'AccountAlias': alias}
        return self.get_response('CreateAccountAlias', params)

    def delete_account_alias(self, alias):
        """
        Deletes an alias for the AWS account.

        For more information on account id aliases, please see
        http://goo.gl/ToB7G

        :type alias: string
        :param alias: The alias to remove from the account.
        """
        params = {'AccountAlias': alias}
        return self.get_response('DeleteAccountAlias', params)

    def get_account_alias(self):
        """
        Get the alias for the current account.

        This is referred to in the docs as list_account_aliases,
        but it seems you can only have one account alias currently.

        For more information on account id aliases, please see
        http://goo.gl/ToB7G
        """
        return self.get_response('ListAccountAliases', {},
                                 list_marker='AccountAliases')

    def get_signin_url(self, service='ec2'):
        """
        Get the URL where IAM users can use their login profile to sign in
        to this account's console.

        :type service: string
        :param service: Default service to go to in the console.
        """
        alias = self.get_account_alias()
        if not alias:
            raise Exception('No alias associated with this account.  Please use iam.create_account_alias() first.')

        if self.host == 'iam.us-gov.amazonaws.com':
            return "https://%s.signin.amazonaws-us-gov.com/console/%s" % (alias, service)
        else:
            return "https://%s.signin.aws.amazon.com/console/%s" % (alias, service)

    def get_account_summary(self):
        """
        Get the alias for the current account.

        This is referred to in the docs as list_account_aliases,
        but it seems you can only have one account alias currently.

        For more information on account id aliases, please see
        http://goo.gl/ToB7G
        """
        return self.get_object('GetAccountSummary', {}, SummaryMap)

    #
    # IAM Roles
    #

    def add_role_to_instance_profile(self, instance_profile_name, role_name):
        """
        Adds the specified role to the specified instance profile.

        :type instance_profile_name: string
        :param instance_profile_name: Name of the instance profile to update.

        :type role_name: string
        :param role_name: Name of the role to add.
        """
        return self.get_response('AddRoleToInstanceProfile',
                                 {'InstanceProfileName': instance_profile_name,
                                  'RoleName': role_name})

    def create_instance_profile(self, instance_profile_name, path=None):
        """
        Creates a new instance profile.

        :type instance_profile_name: string
        :param instance_profile_name: Name of the instance profile to create.

        :type path: string
        :param path: The path to the instance profile.
        """
        params = {'InstanceProfileName': instance_profile_name}
        if path is not None:
            params['Path'] = path
        return self.get_response('CreateInstanceProfile', params)

    def create_role(self, role_name, assume_role_policy_document=None, path=None):
        """
        Creates a new role for your AWS account.

        The policy grants permission to an EC2 instance to assume the role.
        The policy is URL-encoded according to RFC 3986. Currently, only EC2
        instances can assume roles.

        :type role_name: string
        :param role_name: Name of the role to create.

        :type assume_role_policy_document: string
        :param assume_role_policy_document: The policy that grants an entity
            permission to assume the role.

        :type path: string
        :param path: The path to the instance profile.
        """
        params = {'RoleName': role_name}
        if assume_role_policy_document is None:
            # This is the only valid assume_role_policy_document currently, so
            # this is used as a default value if no assume_role_policy_document
            # is provided.
            params['AssumeRolePolicyDocument'] =  ASSUME_ROLE_POLICY_DOCUMENT
        else:
            params['AssumeRolePolicyDocument'] =  assume_role_policy_document
        if path is not None:
            params['Path'] = path
        return self.get_response('CreateRole', params)

    def delete_instance_profile(self, instance_profile_name):
        """
        Deletes the specified instance profile. The instance profile must not
        have an associated role.

        :type instance_profile_name: string
        :param instance_profile_name: Name of the instance profile to delete.
        """
        return self.get_response(
            'DeleteInstanceProfile',
            {'InstanceProfileName': instance_profile_name})

    def delete_role(self, role_name):
        """
        Deletes the specified role. The role must not have any policies
        attached.

        :type role_name: string
        :param role_name: Name of the role to delete.
        """
        return self.get_response('DeleteRole', {'RoleName': role_name})

    def delete_role_policy(self, role_name, policy_name):
        """
        Deletes the specified policy associated with the specified role.

        :type role_name: string
        :param role_name: Name of the role associated with the policy.

        :type policy_name: string
        :param policy_name: Name of the policy to delete.
        """
        return self.get_response(
            'DeleteRolePolicy',
            {'RoleName': role_name, 'PolicyName': policy_name})

    def get_instance_profile(self, instance_profile_name):
        """
        Retrieves information about the specified instance profile, including
        the instance profile's path, GUID, ARN, and role.

        :type instance_profile_name: string
        :param instance_profile_name: Name of the instance profile to get
            information about.
        """
        return self.get_response('GetInstanceProfile', {'InstanceProfileName':
                                                       instance_profile_name})

    def get_role(self, role_name):
        """
        Retrieves information about the specified role, including the role's
        path, GUID, ARN, and the policy granting permission to EC2 to assume
        the role.

        :type role_name: string
        :param role_name: Name of the role associated with the policy.
        """
        return self.get_response('GetRole', {'RoleName': role_name})

    def get_role_policy(self, role_name, policy_name):
        """
        Retrieves the specified policy document for the specified role.

        :type role_name: string
        :param role_name: Name of the role associated with the policy.

        :type policy_name: string
        :param policy_name: Name of the policy to get.
        """
        return self.get_response('GetRolePolicy',
                                 {'RoleName': role_name,
                                  'PolicyName': policy_name})

    def list_instance_profiles(self, path_prefix=None, marker=None,
                               max_items=None):
        """
        Lists the instance profiles that have the specified path prefix. If
        there are none, the action returns an empty list.

        :type path_prefix: string
        :param path_prefix: The path prefix for filtering the results. For
            example: /application_abc/component_xyz/, which would get all
            instance profiles whose path starts with
            /application_abc/component_xyz/.

        :type marker: string
        :param marker: Use this parameter only when paginating results, and
            only in a subsequent request after you've received a response
            where the results are truncated. Set it to the value of the
            Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this parameter only when paginating results to
            indicate the maximum number of user names you want in the response.
        """
        params = {}
        if path_prefix is not None:
            params['PathPrefix'] = path_prefix
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items

        return self.get_response('ListInstanceProfiles', params,
                                 list_marker='InstanceProfiles')

    def list_instance_profiles_for_role(self, role_name, marker=None,
                                        max_items=None):
        """
        Lists the instance profiles that have the specified associated role. If
        there are none, the action returns an empty list.

        :type role_name: string
        :param role_name: The name of the role to list instance profiles for.

        :type marker: string
        :param marker: Use this parameter only when paginating results, and
            only in a subsequent request after you've received a response
            where the results are truncated. Set it to the value of the
            Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this parameter only when paginating results to
            indicate the maximum number of user names you want in the response.
        """
        params = {'RoleName': role_name}
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.get_response('ListInstanceProfilesForRole', params,
                                 list_marker='InstanceProfiles')

    def list_role_policies(self, role_name, marker=None, max_items=None):
        """
        Lists the names of the policies associated with the specified role. If
        there are none, the action returns an empty list.

        :type role_name: string
        :param role_name: The name of the role to list policies for.

        :type marker: string
        :param marker: Use this parameter only when paginating results, and
            only in a subsequent request after you've received a response
            where the results are truncated. Set it to the value of the
            marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this parameter only when paginating results to
            indicate the maximum number of user names you want in the response.
        """
        params = {'RoleName': role_name}
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.get_response('ListRolePolicies', params,
                                 list_marker='PolicyNames')

    def list_roles(self, path_prefix=None, marker=None, max_items=None):
        """
        Lists the roles that have the specified path prefix. If there are none,
        the action returns an empty list.

        :type path_prefix: string
        :param path_prefix: The path prefix for filtering the results.

        :type marker: string
        :param marker: Use this parameter only when paginating results, and
            only in a subsequent request after you've received a response
            where the results are truncated. Set it to the value of the
            marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this parameter only when paginating results to
            indicate the maximum number of user names you want in the response.
        """
        params = {}
        if path_prefix is not None:
            params['PathPrefix'] = path_prefix
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.get_response('ListRoles', params, list_marker='Roles')

    def put_role_policy(self, role_name, policy_name, policy_document):
        """
        Adds (or updates) a policy document associated with the specified role.

        :type role_name: string
        :param role_name: Name of the role to associate the policy with.

        :type policy_name: string
        :param policy_name: Name of the policy document.

        :type policy_document: string
        :param policy_document: The policy document.
        """
        return self.get_response('PutRolePolicy',
                                 {'RoleName': role_name,
                                  'PolicyName': policy_name,
                                  'PolicyDocument': policy_document})

    def remove_role_from_instance_profile(self, instance_profile_name,
                                          role_name):
        """
        Removes the specified role from the specified instance profile.

        :type instance_profile_name: string
        :param instance_profile_name: Name of the instance profile to update.

        :type role_name: string
        :param role_name: Name of the role to remove.
        """
        return self.get_response('RemoveRoleFromInstanceProfile',
                                 {'InstanceProfileName': instance_profile_name,
                                  'RoleName': role_name})

    def update_assume_role_policy(self, role_name, policy_document):
        """
        Updates the policy that grants an entity permission to assume a role.
        Currently, only an Amazon EC2 instance can assume a role.

        :type role_name: string
        :param role_name: Name of the role to update.

        :type policy_document: string
        :param policy_document: The policy that grants an entity permission to
            assume the role.
        """
        return self.get_response('UpdateAssumeRolePolicy',
                                 {'RoleName': role_name,
                                  'PolicyDocument': policy_document})
