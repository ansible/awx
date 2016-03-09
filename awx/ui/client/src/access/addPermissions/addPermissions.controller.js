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

export default ['$rootScope', '$scope', 'GetBasePath', 'Rest', '$q', 'Wait', 'ProcessErrors', function (rootScope, scope, GetBasePath, Rest, $q, Wait, ProcessErrors) {
    var manuallyUpdateChecklists = function(list, id, isSelected) {
        var elemScope = angular
            .element("#" +
                list + "s_table #" + id + ".List-tableRow input")
            .scope();
        if (elemScope) {
            elemScope.isSelected = !!isSelected;
        }
    };

    scope.allSelected = [];

    // the object permissions are being added to
    scope.object = scope[scope.$parent.list
        .iterator + "_obj"];

    // array for all possible roles for the object
    scope.roles = Object
        .keys(scope.object.summary_fields.roles)
        .map(function(key) {
            return {
                value: scope.object.summary_fields
                    .roles[key].id,
                label: scope.object.summary_fields
                    .roles[key].name };
        });

    // TODO: get working with api
    // array w roles and descriptions for key
    scope.roleKey = Object
        .keys(scope.object.summary_fields.roles)
        .map(function(key) {
            return {
                name: scope.object.summary_fields
                    .roles[key].name,
                description: scope.object.summary_fields
                    .roles[key].description };
        });

    // handle form tab changes
    scope.toggleFormTabs = function(list) {
        scope.usersSelected = (list === 'users');
        scope.teamsSelected = !scope.usersSelected;
    };

    // manually handle selection/deselection of user/team checkboxes
    scope.$on("selectedOrDeselected", function(e, val) {
        val = val.value;
        if (val.isSelected) {
            // deselected, so remove from the allSelected list
            scope.allSelected = scope.allSelected.filter(function(i) {
                // return all but the object who has the id and type
                // of the element to deselect
                return (!(val.id === i.id && val.type === i.type));
            });
        } else {
            // selected, so add to the allSelected list
            scope.allSelected.push({
                name: function() {
                    if (val.type === "user") {
                        return (val.first_name &&
                            val.last_name) ?
                            val.first_name + " " +
                            val.last_name :
                            val.username;
                    } else {
                        return val .name;
                    }
                },
                type: val.type,
                roles: [],
                id: val.id
            });
        }
    });

    // used to handle changes to the itemsSelected scope var on "next page",
    // "sorting etc."
    scope.$on("itemsSelected", function(e, inList) {
        // compile a list of objects that needed to be checked in the lists
        scope.updateLists = scope.allSelected.filter(function(inMemory) {
            var notInList = true;
            inList.forEach(function(val) {
                // if the object is part of the allSelected list and is
                // selected,
                // you don't need to add it updateLists
                if (inMemory.id === val.id &&
                    inMemory.type === val.type) {
                    notInList = false;
                }
            });
            return notInList;
        });
    });

    // handle changes to the updatedLists by manually selected those values in
    // the UI
    scope.$watch("updateLists", function(toUpdate) {
        (toUpdate || []).forEach(function(obj) {
            manuallyUpdateChecklists(obj.type, obj.id, true);
        });

        delete scope.updateLists;
    });

    // remove selected user/team
    scope.removeObject = function(obj) {
        manuallyUpdateChecklists(obj.type, obj.id, false);

        scope.allSelected = scope.allSelected.filter(function(i) {
            return (!(obj.id === i.id && obj.type === i.type));
        });
    };

    // update post url list
    scope.$watch("allSelected", function(val) {
        scope.posts = _
            .flatten((val || [])
            .map(function (owner) {
                var url = GetBasePath(owner.type + "s") + owner.id +
                    "/roles/";

                return (owner.roles || [])
                    .map(function (role) {
                        return {url: url,
                            id: role.value};
                });
        }));
    }, true);

    // post roles to api
    scope.updatePermissions = function() {
        Wait('start');

        var requests = scope.posts
            .map(function(post) {
                Rest.setUrl(post.url);
                return Rest.post({"id": post.id});
            });

        $q.all(requests)
            .then(function () {
                Wait('stop');
                rootScope.$broadcast("refreshList", "permission");
                scope.closeModal();
            }, function (error) {
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
