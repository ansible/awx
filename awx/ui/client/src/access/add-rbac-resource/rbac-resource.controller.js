/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Access
 * @description
 * Controller for handling permissions adding
 */

export default ['$rootScope', '$scope', 'GetBasePath', 'Rest', '$q', 'Wait', 'ProcessErrors', function(rootScope, scope, GetBasePath, Rest, $q, Wait, ProcessErrors) {

    init();

    function init(){

        let resources = ['users', 'teams'];

        scope.allSelected = {};
        _.each(resources, (type) => scope.allSelected[type] = {});

        // the object permissions are being added to
        scope.object = scope.resourceData.data;
        // array for all possible roles for the object
        scope.roles = angular.copy(scope.object.summary_fields.object_roles);

        scope.appStrings = rootScope.appStrings;

        const objectType = _.get(scope, ['object', 'type']);
        const teamRoles = _.get(scope, ['object', 'summary_fields', 'object_roles'], {});

        if (objectType === 'organization') {
            // some organization object_roles aren't allowed for teams
            delete teamRoles.admin_role;
            delete teamRoles.member_role;
        }

        scope.teamRoles = teamRoles;

        // TODO: get working with api
        // array w roles and descriptions for key
        scope.roleKey = Object
            .keys(scope.object.summary_fields.object_roles)
            .map(function(key) {
                return {
                    name: scope.object.summary_fields
                        .object_roles[key].name,
                    description: scope.object.summary_fields
                        .object_roles[key].description
                };
            });

        scope.showKeyPane = false;

        scope.tab = {
            users: true,
            teams: false,
        };

        // pop/push into unified collection of selected users & teams
        scope.$on("selectedOrDeselected", function(e, value) {
            let resourceType = scope.currentTab(),
                item = value.value;

            function buildName(user) {
                return (user.first_name &&
                    user.last_name) ?
                    user.first_name + " " +
                    user.last_name :
                    user.username;
            }

            if (value.isSelected) {
                if (item.type === 'user') {
                    item.name = buildName(item);
                }
                scope.allSelected[resourceType][item.id] = item;
                scope.allSelected[resourceType][item.id].roles = [];
            } else {
                delete scope.allSelected[resourceType][item.id];
            }
        });

    }

    scope.currentTab = function(){
        return _.findKey(scope.tab, (tab) => tab);
    };

    scope.removeObject = function(obj){
        let resourceType = scope.currentTab();
        delete scope.allSelected[resourceType][obj.id];
        obj.isSelected = false;
    };

    scope.toggleKeyPane = function() {
        scope.showKeyPane = !scope.showKeyPane;
    };

    scope.hasSelectedRows = function(){
        return _.some(scope.allSelected, (type) => Object.keys(type).length > 0);
    };

    scope.selectTab = function(selected){
        _.each(scope.tab, (value, key, collection) => {
           collection[key] = (selected === key);
        });
    };

    // post roles to api
    scope.updatePermissions = function() {
        Wait('start');

        let requests = [];

        _.forEach(scope.allSelected, (selectedValues) => {
            _.forEach(selectedValues, (selectedValue) => {
                var url = GetBasePath(selectedValue.type + "s") + selectedValue.id +
                    "/roles/";

                if (scope.onlyMemberRole === 'true') {
                    Rest.setUrl(url);
                    requests.push(Rest.post({ "id": scope.roles.member_role.id }));
                } else {
                    (selectedValue.roles || [])
                        .map(function(role) {
                            Rest.setUrl(url);
                            requests.push(Rest.post({ "id": role.value || role.id }));
                        });
                }
            });
        });

        $q.all(requests)
            .then(function() {
                Wait('stop');
                rootScope.$broadcast("refreshList", "permission");
                scope.closeModal();
            }, function(error) {
                Wait('stop');
                rootScope.$broadcast("refreshList", "permission");
                scope.closeModal();
                ProcessErrors(null, error.data, error.status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to post role(s): POST returned status' +
                        error.status
                });
            });
    };
}];
