/*************************************************
 * Copyright (c) 2016 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default ['$scope', '$rootScope', '$compile', '$location',
    '$log', '$stateParams', 'OrganizationForm', 'GenerateForm', 'Rest', 'Alert',
    'ProcessErrors', 'RelatedSearchInit', 'RelatedPaginateInit', 'Prompt',
    'ClearScope', 'GetBasePath', 'Wait', '$state', 'NotificationsListInit',
    'ToggleNotification',
    function($scope, $rootScope, $compile, $location, $log,
        $stateParams, OrganizationForm, GenerateForm, Rest, Alert, ProcessErrors,
        RelatedSearchInit, RelatedPaginateInit, Prompt, ClearScope, GetBasePath,
        Wait, $state, NotificationsListInit, ToggleNotification) {

        ClearScope();

        // Inject dynamic view
        var form = OrganizationForm(),
            generator = GenerateForm,
            defaultUrl = GetBasePath('organizations'),
            base = $location.path().replace(/^\//, '').split('/')[0],
            master = {},
            id = $stateParams.organization_id,
            relatedSets = {};

        $scope.$parent.activeMode = 'edit';

        $scope.$emit("HideOrgListHeader");

        $scope.$emit("ReloadOrganzationCards", id);

        $scope.organization_id = id;

        generator.inject(form, { mode: 'edit', related: true, scope: $scope});
        generator.reset();

        // After the Organization is loaded, retrieve each related set
        if ($scope.organizationLoadedRemove) {
            $scope.organizationLoadedRemove();
        }
        $scope.organizationLoadedRemove = $scope.$on('organizationLoaded', function () {
            for (var set in relatedSets) {
                $scope.search(relatedSets[set].iterator);
            }
            Wait('stop');
            NotificationsListInit({
                scope: $scope,
                url: defaultUrl,
                id: id
            });
        });

        // Retrieve detail record and prepopulate the form
        Wait('start');
        Rest.setUrl(defaultUrl + id + '/');
        Rest.get()
            .success(function (data) {
                var fld, related, set;
                $scope.organization_name = data.name;
                for (fld in form.fields) {
                    if (data[fld]) {
                        $scope[fld] = data[fld];
                        master[fld] = data[fld];
                    }
                }
                related = data.related;
                for (set in form.related) {
                    if (related[set]) {
                        relatedSets[set] = {
                            url: related[set],
                            iterator: form.related[set].iterator
                        };
                    }
                }

                angular.extend(relatedSets, form
                    .relatedSets(data.related));
                // Initialize related search functions. Doing it here to make sure relatedSets object is populated.
                RelatedSearchInit({ scope: $scope, form: form, relatedSets: relatedSets });
                RelatedPaginateInit({ scope: $scope, relatedSets: relatedSets });
                $scope.organization_obj = data;
                $scope.$emit('organizationLoaded');
            })
            .error(function (data, status) {
                ProcessErrors($scope, data, status, form, { hdr: 'Error!',
                    msg: 'Failed to retrieve organization: ' + $stateParams.id + '. GET status: ' + status });
            });

        $scope.toggleNotification = function(event, id, column) {
            var notifier = this.notification;
            try {
                $(event.target).tooltip('hide');
            }
            catch(e) {
                // ignore
            }
            ToggleNotification({
                scope: $scope,
                url: defaultUrl,
                id: $scope.organization_id,
                notifier: notifier,
                column: column,
                callback: 'NotificationRefresh'
            });
        };

        // Save changes to the parent
        $scope.formSave = function () {
            var fld, params = {};
            generator.clearApiErrors();
            Wait('start');
            for (fld in form.fields) {
                params[fld] = $scope[fld];
            }
            Rest.setUrl(defaultUrl + id + '/');
            Rest.put(params)
                .success(function (data) {
                    Wait('stop');
                    $scope.organization_name = $scope.name;
                    master = params;
                    $rootScope.flashMessage = "Your changes were successfully saved!";
                    $scope.$emit("ReloadOrganzationCards", data.id);
                })
                .error(function (data, status) {
                    ProcessErrors($scope, data, status, OrganizationForm, { hdr: 'Error!',
                        msg: 'Failed to update organization: ' + id + '. PUT status: ' + status });
                });
        };

        $scope.formCancel = function () {
            $scope.$emit("ReloadOrganzationCards");
            $scope.$emit("ShowOrgListHeader");
            $state.transitionTo('organizations');
        };

        // Related set: Add button
        $scope.add = function (set) {
            $rootScope.flashMessage = null;
            $location.path('/' + base + '/' + $stateParams.organization_id + '/' + set);
        };

        // Related set: Edit button
        $scope.edit = function (set, id) {
            $rootScope.flashMessage = null;
            $location.path('/' + set + '/' + id);
        };

        // Related set: Delete button
        $scope['delete'] = function (set, itm_id, name, title) {
            $rootScope.flashMessage = null;

            var action = function () {
                Wait('start');
                var url = defaultUrl + $stateParams.organization_id + '/' + set + '/';
                Rest.setUrl(url);
                Rest.post({ id: itm_id, disassociate: 1 })
                    .success(function () {
                        $('#prompt-modal').modal('hide');
                        $scope.search(form.related[set].iterator);
                    })
                    .error(function (data, status) {
                        $('#prompt-modal').modal('hide');
                        ProcessErrors($scope, data, status, null, { hdr: 'Error!',
                            msg: 'Call to ' + url + ' failed. POST returned status: ' + status });
                    });
            };

            Prompt({
                hdr: 'Delete',
                body: '<div class="Prompt-bodyQuery">Are you sure you want to remove the ' + title + ' below from ' + $scope.name + '?</div><div class="Prompt-bodyTarget">' + name + '</div>',
                action: action,
                actionText: 'DELETE'
            });

        };
}
];
