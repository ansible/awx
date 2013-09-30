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
from boto.exception import JSONResponseError


class ClusterNotFoundFault(JSONResponseError):
    pass


class InvalidClusterSnapshotStateFault(JSONResponseError):
    pass


class ClusterSnapshotNotFoundFault(JSONResponseError):
    pass


class ClusterNotFoundFault(JSONResponseError):
    pass


class ClusterSecurityGroupQuotaExceededFault(JSONResponseError):
    pass


class ReservedNodeOfferingNotFoundFault(JSONResponseError):
    pass


class InvalidSubnet(JSONResponseError):
    pass


class ClusterSubnetGroupQuotaExceededFault(JSONResponseError):
    pass


class InvalidClusterStateFault(JSONResponseError):
    pass


class InvalidClusterParameterGroupStateFault(JSONResponseError):
    pass


class ClusterParameterGroupAlreadyExistsFault(JSONResponseError):
    pass


class InvalidClusterSecurityGroupStateFault(JSONResponseError):
    pass


class InvalidRestoreFault(JSONResponseError):
    pass


class AuthorizationNotFoundFault(JSONResponseError):
    pass


class ResizeNotFoundFault(JSONResponseError):
    pass


class NumberOfNodesQuotaExceededFault(JSONResponseError):
    pass


class ClusterSnapshotAlreadyExistsFault(JSONResponseError):
    pass


class AuthorizationQuotaExceededFault(JSONResponseError):
    pass


class AuthorizationAlreadyExistsFault(JSONResponseError):
    pass


class ClusterSnapshotQuotaExceededFault(JSONResponseError):
    pass


class ReservedNodeNotFoundFault(JSONResponseError):
    pass


class ReservedNodeAlreadyExistsFault(JSONResponseError):
    pass


class ClusterSecurityGroupAlreadyExistsFault(JSONResponseError):
    pass


class ClusterParameterGroupNotFoundFault(JSONResponseError):
    pass


class ReservedNodeQuotaExceededFault(JSONResponseError):
    pass


class ClusterQuotaExceededFault(JSONResponseError):
    pass


class ClusterSubnetQuotaExceededFault(JSONResponseError):
    pass


class UnsupportedOptionFault(JSONResponseError):
    pass


class InvalidVPCNetworkStateFault(JSONResponseError):
    pass


class ClusterSecurityGroupNotFoundFault(JSONResponseError):
    pass


class InvalidClusterSubnetGroupStateFault(JSONResponseError):
    pass


class ClusterSubnetGroupAlreadyExistsFault(JSONResponseError):
    pass


class NumberOfNodesPerClusterLimitExceededFault(JSONResponseError):
    pass


class ClusterSubnetGroupNotFoundFault(JSONResponseError):
    pass


class ClusterParameterGroupQuotaExceededFault(JSONResponseError):
    pass


class ClusterAlreadyExistsFault(JSONResponseError):
    pass


class InsufficientClusterCapacityFault(JSONResponseError):
    pass


class InvalidClusterSubnetStateFault(JSONResponseError):
    pass


class SubnetAlreadyInUse(JSONResponseError):
    pass


class InvalidParameterCombinationFault(JSONResponseError):
    pass


class AccessToSnapshotDeniedFault(JSONResponseError):
    pass


class UnauthorizedOperationFault(JSONResponseError):
    pass
