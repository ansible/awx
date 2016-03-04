/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

/**
 * @ngdoc function
 * @name controllers.function:Authentication
 * @description
 * Controller for handling /#/login and /#/logout routes.
 *
 * Tower (app.js) verifies the user is authenticated and that the user session is not expired. If either condition is not true,
 * the user is redirected to /#/login and the Authentication controller.
 *
 * Methods for checking the session state are found in [js/shared/AuthService.js](/static/docs/api/shared.function:AuthService), which is referenced here as Authorization.
 *
 * #Login Modal Dialog
 *
 * The modal dialog prompting for username and password is found in templates/ui/index.html.
 *```
 *     <!-- login modal -->
 *     <div id="login-modal" class="modal fade">
 *         <div class="modal-dialog">
 *             <div class="modal-content" id="login-modal-content">
 *             </div><!-- modal-content -->
 *         </div><!-- modal-dialog -->
 *     </div><!-- modal -->
 *```
 * HTML for the login form is generated, compiled and injected into <div id="login-modal-content"></div> by the controller. This is done to associate the form with the controller's scope. Because
 * <div id="login-modal"></div> is outside of the ng-view container, it gets associated with $rootScope by default. In the controller we create a new scope using $rootScope.$new() and associate
 * that with the login form. Doing this each time the controller is instantiated insures the form is clean and not pre-populated with a prior user's username and password.
 *
 * Just before the release of 2.0 a bug was discovered where clicking logout and then immediately clicking login without providing a username and password would successfully log
 * the user back into Tower. Implementing the above approach fixed this, forcing a new username/password to be entered each time the login dialog appears.
 *
 * #Login Workflow
 *
 * When the the login button is clicked, the following occurs:
 *
 * - Call Authorization.retrieveToken(username, password) - sends a POST request to /api/v1/authtoken to get a new token value.
 * - Call Authorization.setToken(token, expires) to store the token and exipration time in a session cookie.
 * - Start the expiration timer by calling the init() method of [js/shared/Timer.js](/static/docs/api/shared.function:Timer)
 * - Get user informaton by calling Authorization.getUser() - sends a GET request to /api/v1/me
 * - Store user information in the session cookie by calling Authorization.setUser().
 * - Get the Tower license by calling Authorization.getLicense() - sends a GET request to /api/vi/config
 * - Stores the license object in local storage by calling Authorization.setLicense(). This adds the Tower version and a tested flag to the license object. The tested flag is initially set to false.
 *
 * Note that there is a session timer kept on the server side as well as the client side. Each time an API request is made, Tower (in app.js) calls
 * Timer.isExpired(). This verifies the UI does not think the session is expired, and if not, moves the expiration time into the future. The number of
 * seconds between API calls before a session is considered expired is set in config.js as session_timeout.
 *
 * @Usage
 * This is usage information.
 */

export default ['$rootScope', '$scope', 'GetBasePath', 'Rest', '$q', function (rootScope, scope, GetBasePath, Rest, $q) {
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

    // handle form tabs
    scope.toggleFormTabs = function(list) {
        scope.usersSelected = (list === 'users');
        scope.teamsSelected = !scope.usersSelected;
    };

    // TODO: manually handle selection/deselection
    // of user/team checkboxes
    scope.$on("selectedOrDeselected", function(e, val) {
        val = val.value;
        if (val.isSelected) {
            scope.allSelected = scope.allSelected.filter(function(i) {
                return (!(val.id === i.id && val.type === i.type));
            });
        } else {
            var name;

            if (val.type === "user") {
                name = (val.first_name &&
                    val.last_name) ?
                    val.first_name + " " +
                    val.last_name :
                    val.username;
            } else {
                name = val.name;
            }

            scope.allSelected.push({
                name: name,
                type: val.type,
                roles: [],
                id: val.id
            });
        }
    });

    scope.$on("itemsSelected", function(e, inList) {
        scope.updateLists = scope.allSelected.filter(function(inMemory) {
            var notInList = true;
            inList.forEach(function(val) {
                if (inMemory.id === val.id &&
                    inMemory.type === val.type) {
                    notInList = false;
                }
            });
            return notInList;
        });
    });

    scope.$watch("updateLists", function(toUpdate) {
        (toUpdate || []).forEach(function(obj) {
            var elemScope = angular
                .element("#" +
                    obj.type + "s_table #" + obj.id +
                    ".List-tableRow input")
                .scope()
            if (elemScope) {
                elemScope.isSelected = true;
            }
        });

        delete scope.updateLists;
    });

    // create array of users/teams
    // scope.$watchGroup(['selectedUsers', 'selectedTeams'],
    //     function(val) {
    //         scope.allSelected = (val[0] || [])
    //             .map(function(i) {
    //                 var roles = i.roles || [];
    //                 var name = (i.first_name &&
    //                     i.last_name) ?
    //                     i.first_name + " " +
    //                     i.last_name :
    //                     i.username;
    //
    //                 return {
    //                     name: name,
    //                     type: "user",
    //                     roles: roles,
    //                     id: i.id
    //                 };
    //         }).concat((val[1] || [])
    //             .map(function(i) {
    //                 var roles = i.roles || [];
    //
    //                 return {
    //                     name: i.name,
    //                     type: "team",
    //                     roles: roles,
    //                     id: i.id
    //                 };
    //         }));
    // });

    // remove selected user/team
    scope.removeObject = function(obj) {
        var elemScope = angular
            .element("#" +
                obj.type + "s_table #" + obj.id + ".List-tableRow input")
            .scope()
        if (elemScope) {
            elemScope.isSelected = false;
        }

        scope.allSelected = scope.allSelected.filter(function(i) {
            return (!(obj.id === i.id && obj.type === i.type));
        });
    };

    // update post url list
    scope.$watch("allSelected", function(val) {
        scope.posts = _
            .flatten((val || [])
            .map(function (owner) {
                var url = GetBasePath(owner.type + "s") + "/" + owner.id +
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
        var requests = scope.posts
            .map(function(post) {
                Rest.setUrl(post.url);
                return Rest.post({"id": post.id});
            });

        $q.all(requests)
            .then(function (responses) {
                rootScope.$broadcast("refreshList", "permission");
                scope.closeModal();
            }, function (error) {
                // TODO: request(s) errored out.  Call process errors
            });
    };
}];
