export default ['templateUrl', '$window', function(templateUrl, $window) {
    return {
        restrict: 'E',
        scope: {
            galaxyCredentials: '='
        },
        templateUrl: templateUrl('organizations/galaxy-credentials-multiselect/galaxy-credentials-modal/galaxy-credentials-modal'),

        link: function(scope, element) {

            $('#galaxy-credentials-modal').on('hidden.bs.modal', function () {
                $('#galaxy-credentials-modal').off('hidden.bs.modal');
                $(element).remove();
            });

            scope.showModal = function() {
                $('#galaxy-credentials-modal').modal('show');
            };

            scope.destroyModal = function() {
                $('#galaxy-credentials-modal').modal('hide');
            };
        },

        controller: ['$scope', '$compile', 'QuerySet', 'GetBasePath','generateList', 'CredentialList', function($scope, $compile, qs, GetBasePath, GenerateList, CredentialList) {

            function init() {

                    $scope.credential_queryset = {
                        order_by: 'name',
                        page_size: 5,
                        credential_type__kind: 'galaxy'
                    };

                    $scope.credential_default_params = {
                        order_by: 'name',
                        page_size: 5,
                        credential_type__kind: 'galaxy'
                    };

                    qs.search(GetBasePath('credentials'), $scope.credential_queryset)
                        .then(res => {
                            $scope.credential_dataset = res.data;
                            $scope.credentials = $scope.credential_dataset.results;

                            let credentialList = _.cloneDeep(CredentialList);

                            credentialList.listTitle = false;
                            credentialList.well = false;
                            credentialList.multiSelect = true;
                            credentialList.multiSelectPreview = {
                                selectedRows: 'credTags',
                                availableRows: 'credentials'
                            };
                            credentialList.fields.name.ngClick = "linkoutCredential(credential)";
                            credentialList.fields.name.columnClass = 'col-md-11 col-sm-11 col-xs-11';
                            delete credentialList.fields.consumed_capacity;
                            delete credentialList.fields.jobs_running;

                            let html = `${GenerateList.build({
                                list: credentialList,
                                input_type: 'galaxy-credentials-modal-body',
                                hideViewPerPage: true,
                                mode: 'lookup'
                            })}`;

                            $scope.list = credentialList;
                            $('#galaxy-credentials-modal-body').append($compile(html)($scope));

                            if ($scope.galaxyCredentials) {
                                $scope.galaxyCredentials = $scope.galaxyCredentials.map( (item) => {
                                    item.isSelected = true;
                                    if (!$scope.credTags) {
                                        $scope.credTags = [];
                                    }
                                    $scope.credTags.push(item);
                                    return item;
                                });
                            }

                            $scope.showModal();
                    });

                    $scope.$watch('credentials', function(){
                        angular.forEach($scope.credentials, function(credentialRow) {
                            angular.forEach($scope.credTags, function(selectedCredential){
                                if(selectedCredential.id === credentialRow.id) {
                                    credentialRow.isSelected = true;
                                }
                            });
                        });
                    });
            }

            init();

            $scope.$on("selectedOrDeselected", function(e, value) {
                let item = value.value;
                if (value.isSelected) {
                    if(!$scope.credTags) {
                        $scope.credTags = [];
                    }
                    $scope.credTags.push(item);
                } else {
                    _.remove($scope.credTags, { id: item.id });
                }
            });

            $scope.linkoutCredential = function(credential) {
                $window.open('/#/credentials/' + credential.id,'_blank');
            };

            $scope.cancelForm = function() {
                $scope.destroyModal();
            };

            $scope.saveForm = function() {
                $scope.galaxyCredentials = $scope.credTags;
                $scope.destroyModal();
            };
        }]
    };
}];
