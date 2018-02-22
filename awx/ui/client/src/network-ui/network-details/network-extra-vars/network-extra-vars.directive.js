/*************************************************
 * Copyright (c) 2018 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

const templateUrl = require('~network-ui/network-details/network-extra-vars/network-extra-vars.partial.html');

export default [ 'ParseTypeChange', 'ParseVariableString',
    function(ParseTypeChange, ParseVariableString) {
    return {
        scope:{
            item: "="
        },
        templateUrl,
        restrict: 'E',
        link(scope){
            scope.networkingExtraVarsModalOpen = true;
            function init(){
                if(scope.item && scope.item.host_id){
                    scope.variables = ParseVariableString(scope.item.variables);
                    scope.parseType = 'yaml';
                	ParseTypeChange({
                		scope: scope,
                		field_id: 'network_host_variables',
                		variable: 'variables',
                        readOnly: true
                	});
                }
            }

            scope.$watch('item', function(){
                init();
            });

            scope.closeExtraVarModal = function() {
                // Unbind the listener so it doesn't fire when we close the modal via navigation
                $('.CodeMirror')[1].remove();
                $('#NetworkingExtraVarsModal').off('hidden.bs.modal');
                $('#NetworkingExtraVarsModal').modal('hide');
                scope.networkingExtraVarsModalOpen = false;
            };

            scope.openExtraVarsModal = function(){
                scope.networkingExtraVarsModalOpen = true;
                $('#NetworkingExtraVarsModal').modal('show');

                $('.modal-dialog').on('resize', function(){
                    resize();
                });
                scope.extra_variables = ParseVariableString(_.cloneDeep(scope.item.variables));
                scope.parseType = 'yaml';
                ParseTypeChange({
            		scope: scope,
            		field_id: 'NetworkingExtraVars-codemirror',
            		variable: 'extra_variables',
                    readOnly: true
            	});
                resize();
            };

            function resize(){
                let editor = $('.CodeMirror')[1].CodeMirror;
                let height = $('#NetworkingExtraVarsModalDialog').height() - $('.NetworkingExtraVars-header').height() - $('.NetworkingExtraVars-controls').height() - 110;
                editor.setSize("100%", height);
            }

        }
    };
}];
