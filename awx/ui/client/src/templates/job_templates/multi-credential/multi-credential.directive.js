/*************************************************
 * Copyright (c) 2017 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['templateUrl', '$compile',
    function(templateUrl, $compile) {
        return {
            scope: {
                credentials: '=',
                selectedCredentials: '=',
                prompt: '=',
                credentialNotPresent: '=',
                credentialsToPost: '=',
                fieldIsDisabled: '='
            },
            restrict: 'E',
            templateUrl: templateUrl('templates/job_templates/multi-credential/multi-credential'),
            controller: ['$scope', 'MultiCredentialService',
                function($scope, MultiCredentialService) {
                    if (!$scope.selectedCredentials) {
                        $scope.selectedCredentials = {
                            machine: null,
                            vault: null,
                            extra: []
                        };
                    }

                    if (!$scope.credentialsToPost) {
                        $scope.credentialsToPost = [];
                    }

                    $scope.fieldDirty = false;

                    $scope.$watchGroup(['prompt', 'credentialsToPost'],
                        function() {
                            if ($scope.prompt ||
                                $scope.credentialsToPost.length) {
                                    $scope.fieldDirty = true;
                            }

                            $scope.credentialNotPresent = !$scope.prompt &&
                                $scope.selectedCredentials.machine === null &&
                                $scope.selectedCredentials.vault === null;
                    });

                    $scope.removeCredential = function(credToRemove) {
                        [$scope.selectedCredentials,
                            $scope.credentialsToPost] = MultiCredentialService
                                .removeCredential(credToRemove, $scope.
                                    selectedCredentials,
                                        $scope.credentialsToPost);
                    };
                }
            ],
            link: function(scope) {
                scope.openMultiCredentialModal = function() {
                    $('#content-container')
                        .append($compile(`
                            <multi-credential-modal
                                credentials="credentials"
                                credentials-to-post="credentialsToPost"
                                selected-credentials="selectedCredentials">
                            </multi-credential-modal>`)(scope));
                };
            }
        };
    }
];
