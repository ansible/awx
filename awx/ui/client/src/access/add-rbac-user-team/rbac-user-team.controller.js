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

export default ['$scope', '$state', 'i18n', 'CreateSelect2', 'Rest', '$q', 'Wait', 'ProcessErrors', '$rootScope',
function(scope, $state, i18n, CreateSelect2, Rest, $q, Wait, ProcessErrors, rootScope) {

    init();

    function init(){

        scope.appStrings = rootScope.appStrings;

        let resources = ['job_templates', 'workflow_templates', 'projects', 'inventories', 'credentials', 'organizations'];

        // data model:
        // selected - keyed by type of resource
        // selected[type] - keyed by each resource object's id
        // selected[type][id] === { roles: [ ... ], ... }

        // collection of resources selected in section 1
        scope.allSelected = {};
        _.each(resources, (type) => scope.allSelected[type] = {});

        // collection of assignable roles per type of resource
        scope.keys = {};
        _.each(resources, (type) => scope.keys[type] = {});

        // collection of currently-selected role to assign in section 2
        scope.roleSelection = {};
        _.each(resources, (type) => scope.roleSelection[type] = null);

        // tracks currently-selected tabs, initialized with the job templates tab open
        scope.tab = {
            job_templates: true,
            workflow_templates: false,
            projects: false,
            inventories: false,
            credentials: false,
            organizations: false
        };

        // initializes select2 per select field
        // html snippet:
        /*
            <div ng-repeat="(type, roleSet) in keys">
                <select
                    ng-show="tab[type]"
                    id="{{type}}-role-select" class="form-control"
                    ng-model="roleSelection[type]"
                    ng-options="value.name for (key , value) in roleSet">
                </select>
            </div>
        */
        _.each(resources, (type) => buildSelect2(type));

        function buildSelect2(type){
            CreateSelect2({
                element: `#${type}-role-select`,
                multiple: false,
                placeholder: i18n._('Select a role')
            });
        }

        scope.showKeyPane = false;

        // the user or team being assigned permissions
        scope.owner = scope.resolve.resourceData.data;
    }

    // aggregate name/descriptions for each available role, based on resource type
    // reasoning:
    function aggregateKey(item, type) {
        const ownerType = _.get(scope, ['owner', 'type']);
        const { object_roles } = item.summary_fields;

        if (ownerType === 'team' && type === 'organizations') {
            // some organization object_roles aren't allowed for teams
            delete object_roles.admin_role;
            delete object_roles.member_role;
        }

        _.merge(scope.keys[type], object_roles);
    }

    scope.closeModal = function() {
        $state.go('^', null, {reload: true});
    };

    scope.currentTab = function(){
        return _.findKey(scope.tab, (tab) => tab);
    };

    scope.toggleKeyPane = function() {
        scope.showKeyPane = !scope.showKeyPane;
    };

    scope.showSection2Container = function(){
        return _.some(scope.allSelected, (type) => Object.keys(type).length > 0);
    };

    scope.showSection2Tab = function(tab){
        return Object.keys(scope.allSelected[tab]).length > 0;
    };

    scope.saveEnabled = function(){
        let missingRole = false;
        let resourceSelected = false;
        _.forOwn(scope.allSelected, function(value, key) {
            if(Object.keys(value).length > 0) {
                // A resource from this tab has been selected
                resourceSelected = true;
                if(!scope.roleSelection[key]) {
                    missingRole = true;
                }
            }
         });
        return resourceSelected && !missingRole;
    };

    // handle form tab changes
    scope.selectTab = function(selected){
        _.each(scope.tab, (value, key, collection) => {
           collection[key] = (selected === key);
        });
    };

    // pop/push into unified collection of selected resourcesf
    scope.$on("selectedOrDeselected", function(e, value) {
        let resourceType = scope.currentTab(),
            item = value.value;

        if (value.isSelected) {
            scope.allSelected[resourceType][item.id] = item;
            scope.allSelected[resourceType][item.id].roles = [];
            aggregateKey(item, resourceType);
        } else {
            delete scope.allSelected[resourceType][item.id];
        }
    });

    // post roles to api
    scope.saveForm = function() {
        //Wait('start');

        // builds an array of role entities to apply to current user or team
        let roles = _(scope.allSelected).map( (resources, type) => {
            return _.map(resources, (resource) => {
                return resource.summary_fields.object_roles[scope.roleSelection[type]];
            });
        }).flattenDeep().value();

        Rest.setUrl(scope.owner.related.roles);

        $q.all( _.map(roles, (entity) => Rest.post({id: entity.id})) )
            .then( () =>{
                Wait('stop');
                scope.closeModal();
            }, (error) => {
                scope.closeModal();
                ProcessErrors(null, error.data, error.status, null, {
                    hdr: 'Error!',
                    msg: 'Failed to post role(s): POST returned status' +
                        error.status
                });
            });
    };
}];
