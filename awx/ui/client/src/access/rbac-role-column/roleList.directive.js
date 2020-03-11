/* jshint unused: vars */
export default
    [   'templateUrl', 'Wait', 'GetBasePath', 'Rest', '$state', 'ProcessErrors', 'Prompt', '$filter', '$rootScope', 'i18n', 'AppStrings',
        function(templateUrl, Wait, GetBasePath, Rest, $state, ProcessErrors, Prompt, $filter, $rootScope, i18n, strings) {
            return {
                restrict: 'E',
                scope: {
                    'deleteTarget': '='
                },
                templateUrl: templateUrl('access/rbac-role-column/roleList'),
                link: function(scope, element, attrs) {
                    // given a list of roles (things like "project
                    // auditor") which are pulled from two different
                    // places in summary fields, and creates a
                    // concatenated/sorted list
                    scope.access_list = []
                        .concat(scope.deleteTarget.summary_fields
                            .direct_access.map((i) => {
                                i.role.explicit = true;
                                return i.role;
                        }))
                        .concat(scope.deleteTarget.summary_fields
                            .indirect_access.map((i) => {
                                // Indirect access roles describe the role on another object that
                                // gives the user access to this object, so we must introspect them.
                                //
                                // If the user has indirect admin access, they are system admin, org admin,
                                // or a <resource_type>_admin. Return the role name directly.
                                // Similarly, if they are an auditor, return that instead of a read role.
                                if (i.descendant_roles.includes('admin_role') || i.role.name.includes('Auditor')) {
                                    i.role.explicit = false;
                                    i.role.parent_role_name = i.role.name;
                                    return i.role;
                                }
                                // Handle more complex cases
                                // This includes roles team<->team roles, and roles an org admin
                                // inherits from teams in their organization.
                                //
                                // For these, we want to describe the actual permissions for the
                                // object we are retrieving the access_list for, so replace
                                // the role name with the descendant_roles.
                                let indirect_roles = [];
                                i.descendant_roles.forEach((descendant_role) => {
                                    let r = _.cloneDeep(i.role);
                                    r.parent_role_name = r.name;
                                    r.name = descendant_role.replace('_role','');
                                    r.explicit = false;
                                    // Do not include the read role unless it is the only descendant role.
                                    if (r.name !== 'read' || i.descendant_roles.length === 1) {
                                        indirect_roles.push(r);
                                    }
                                });
                                return indirect_roles;
                        }))
                        .flat()
                        .filter((role) => {
                            return Boolean(attrs.teamRoleList) === Boolean(role.team_id);
                        })
                        .sort((a, b) => {
                            if (a.name
                                .toLowerCase() > b.name
                                    .toLowerCase()) {
                                return 1;
                            } else {
                                return -1;
                            }
                        });

                    scope.deletePermission = function(user, accessListEntry) {
                        let entry = accessListEntry;

                        let action = function() {
                            $('#prompt-modal').modal('hide');
                            Wait('start');

                            let url;
                            if (entry.team_id) {
                                url = GetBasePath("teams") + entry.team_id + "/roles/";
                            } else {
                                url = GetBasePath("users") + user.id + "/roles/";
                            }

                            Rest.setUrl(url);
                            Rest.post({ "disassociate": true, "id": entry.id })
                                .then(() => {
                                    Wait('stop');
                                    $state.go('.', null, { reload: true });
                                })
                                .catch(({data, status}) => {
                                    ProcessErrors($rootScope, data, status, null, {
                                        hdr: 'Error!',
                                        msg: 'Failed to remove access.  Call to ' + url + ' failed. DELETE returned status: ' + status
                                    });
                                });
                        };

                        if (accessListEntry.team_id) {
                            Prompt({
                                hdr: strings.get('removeTeamAccess.HEADER'),
                                body: `<div class="Prompt-bodyQuery">${strings.get('removeTeamAccess.CONFIRM', entry.name, $filter('sanitize')(entry.team_name))}</div>`,
                                action: action,
                                actionText: strings.get('removeTeamAccess.ACTION_TEXT'),
                            });
                        } else {
                            Prompt({
                                hdr: strings.get('removeUserAccess.HEADER'),
                                body: `<div class="Prompt-bodyQuery">${strings.get('removeUserAccess.CONFIRM', entry.name, $filter('sanitize')(user.username))}</div>`,
                                action: action,
                                actionText: strings.get('removeUserAccess.ACTION_TEXT'),
                            });
                        }
                    };
                }
            };
        }
    ];
