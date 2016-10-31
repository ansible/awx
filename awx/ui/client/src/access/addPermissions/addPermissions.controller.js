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

    scope.allSelected = [];

    // the object permissions are being added to
    scope.object = scope.resourceData.data;
    // array for all possible roles for the object
    scope.roles = Object
        .keys(scope.object.summary_fields.object_roles)
        .map(function(key) {
            return {
                value: scope.object.summary_fields
                    .object_roles[key].id,
                label: scope.object.summary_fields
                    .object_roles[key].name
            };
        });

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

    scope.toggleKeyPane = function() {
        scope.showKeyPane = !scope.showKeyPane;
    };

    // handle form tab changes
    scope.toggleFormTabs = function(list) {
        scope.usersSelected = (list === 'users');
        scope.teamsSelected = !scope.usersSelected;
    };

    // pop/push into unified collection of selected users & teams
    scope.$on("selectedOrDeselected", function(e, value) {
        let item = value.value;

        function buildName(user) {
            return (user.first_name &&
                user.last_name) ?
                user.first_name + " " +
                user.last_name :
                user.username;
        }

        if (item.isSelected) {
            if (item.type === 'user') {
                item.name = buildName(item);
            }
            scope.allSelected.push(item);
        } else {
            scope.allSelected = _.remove(scope.allSelected, { id: item.id });
        }
    });

    // update post url list
    scope.$watch("allSelected", function(val) {
        scope.posts = _
            .flatten((val || [])
                .map(function(owner) {
                    var url = GetBasePath(owner.type + "s") + owner.id +
                        "/roles/";

                    return (owner.roles || [])
                        .map(function(role) {
                            return {
                                url: url,
                                id: role.value
                            };
                        });
                }));
    }, true);

    // post roles to api
    scope.updatePermissions = function() {
        Wait('start');

        var requests = scope.posts
            .map(function(post) {
                Rest.setUrl(post.url);
                return Rest.post({ "id": post.id });
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
