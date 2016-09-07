export default function($stateProvider) {
    this.$get = function() {
        return {
            addSocket: function(state){
                // var resolve = state.resolve || {};
                if(!state.resolve){
                    state.resolve = {};
                }
                state.resolve.socket = ['SocketService', '$rootScope',
                    function(SocketService, $rootScope) {
                        // var self = this;
                        $rootScope.socketPromise.promise.then(function(){
                            SocketService.subscribe2(state);
                            return true;
                        });
                    }]
            },

            addState: function(state) {
                var route = state.route || state.url;

                if(state.socket){
                    this.addSocket(state);
                }

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
