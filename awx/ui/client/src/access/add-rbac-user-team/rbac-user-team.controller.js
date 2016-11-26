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

export default ['$rootScope', '$scope', '$state', 'GetBasePath', 'Rest', '$q', 'Wait', 'ProcessErrors', 
function(rootScope, scope, $state, GetBasePath, Rest, $q, Wait, ProcessErrors) {

    init();

    function init(){

        let resources = ['templates', 'projects', 'inventories', 'credentials'];

        // data model:
        // selected - keyed by type of resource
        // selected[type] - keyed by each resource object's id
        // selected[type][id] === { roles: [ ... ], ... }
        scope.selected = {};
        _.each(resources, (resource) => scope.selected[resource] = {});

        scope.keys = {};
        _.each(resources, (resource) => scope.keys[resource] = {});

        scope.tab = {
            templates: true,
            projects: false,
            inventories: false,
            credentials: false
        };
        scope.showKeyPane = false;
        scope.owner = scope.resolve.resourceData.data;
    }

    // aggregate name/descriptions for each available role, based on resource type
    function aggregateKey(item, type){
        _.merge(scope.keys[type], item.summary_fields.object_roles);
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
        return _.any(scope.selected, (type) => Object.keys(type).length > 0);
    };

    scope.showSection2Tab = function(tab){
        return Object.keys(scope.selected[tab]).length > 0;
    };

    scope.removeSelection = function(resource, type){
        delete scope.selected[type][resource.id];
        resource.isSelected = false;
    };

    // handle form tab changes
    scope.selectTab = function(selected){
        _.each(scope.tab, (value, key, collection) => {
           collection[key] = (selected === key);
        });
    };

    // pop/push into unified collection of selected users & teams
    scope.$on("selectedOrDeselected", function(e, value) {
        let resourceType = scope.currentTab(),
            item = value.value;

        if (item.isSelected) {
            scope.selected[resourceType][item.id] = item;
            scope.selected[resourceType][item.id].roles = [];
            aggregateKey(item, resourceType);
        } else {
            delete scope.selected[resourceType][item.id];
        }
    });

    // post roles to api
    scope.saveForm = function() {
        Wait('start');
        // scope.selected => { n: {id: n}, ... } => [ {id: n}, ... ]
        let requests = _(scope.selected).map((type) => {
            return _.map(type, (resource) => resource.roles);
        }).flattenDeep().value();
        
        Rest.setUrl(scope.owner.related.roles);

        $q.all( _.map(requests, (entity) => Rest.post({id: entity.id})) )
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
