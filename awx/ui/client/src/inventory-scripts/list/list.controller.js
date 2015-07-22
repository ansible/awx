/*************************************************
 * Copyright (c) 2015 Ansible, Inc.
 *
 * All Rights Reserved
 *************************************************/

export default
    [   '$rootScope','Wait', 'generateList', 'inventoryScriptsListObject',
        'GetBasePath' , 'SearchInit' , 'PaginateInit',
        'Rest' , 'ProcessErrors', 'Prompt', 'transitionTo', 'Stream',
        function(
            $rootScope,Wait, GenerateList, inventoryScriptsListObject,
            GetBasePath, SearchInit, PaginateInit,
            Rest, ProcessErrors, Prompt, transitionTo, Stream
        ) {
            var scope = $rootScope.$new(),
                defaultUrl = GetBasePath('inventory_scripts'),
                list = inventoryScriptsListObject,
                view = GenerateList;

            view.inject( list, {
                mode: 'edit',
                scope: scope
            });

            SearchInit({
                scope: scope,
                set: 'inventory_scripts',
                list: list,
                url: defaultUrl
            });
            PaginateInit({
                scope: scope,
                list: list,
                url: defaultUrl
            });

            scope.search(list.iterator);

            scope.editCustomInv = function(){
                transitionTo('inventoryScriptsEdit', {
                    inventory_script: this.inventory_script
                });
            };

            scope.showActivity = function () {
                Stream({ scope: scope });
            };

            scope.deleteCustomInv =  function(id, name){

                var action = function () {
                    $('#prompt-modal').modal('hide');
                    Wait('start');
                    var url = defaultUrl + id + '/';
                    Rest.setUrl(url);
                    Rest.destroy()
                        .success(function () {
                            scope.search(list.iterator);
                        })
                        .error(function (data, status) {
                            ProcessErrors(scope, data, status, null, { hdr: 'Error!',
                                msg: 'Call to ' + url + ' failed. DELETE returned status: ' + status });
                        });
                };

                var bodyHtml = "<div class=\"alert alert-info\">Are you sure you want to delete " + name + "?</div>";
                Prompt({
                    hdr: 'Delete',
                    body: bodyHtml,
                    action: action
                });
            };

            scope.addCustomInv = function(){
                transitionTo('inventoryScriptsAdd');
            };

        }
    ];
