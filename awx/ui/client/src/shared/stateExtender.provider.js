export default function($stateProvider) {
    this.$get = function() {
        return {
            addSocket: function(state){
                if(state.socket!==null){
                    if(!state.resolve){
                        state.resolve = {};
                    }
                    state.resolve.socket = ['SocketService', '$rootScope', '$stateParams',
                        function(SocketService, $rootScope, $stateParams) {
                            $rootScope.socketPromise.promise.then(function(){
                                if(!state.socket){
                                    state.socket = {groups: {}};
                                    SocketService.unsubscribe(state);
                                }
                                else{
                                    if(state.socket.groups.hasOwnProperty( "job_events")){
                                        state.socket.groups.job_events = [$stateParams.id];
                                    }
                                    if(state.socket.groups.hasOwnProperty( "ad_hoc_command_events")){
                                        state.socket.groups.ad_hoc_command_events = [$stateParams.id];
                                    }
                                    SocketService.subscribe(state);
                                }
                                return true;
                            });
                        }];
                }
            },

            addState: function(state) {
                var route = state.route || state.url;
                this.addSocket(state);
                $stateProvider.state(state.name, {
                    url: route,
                    controller: state.controller,
                    templateUrl: state.templateUrl,
                    resolve: state.resolve,
                    params: state.params,
                    data: state.data,
                    ncyBreadcrumb: state.ncyBreadcrumb,
                    onEnter: state.onEnter,
                    onExit: state.onExit,
                    template: state.template,
                    controllerAs: state.controllerAs,
                    views: state.views
                });
            }
        };
    };
}
