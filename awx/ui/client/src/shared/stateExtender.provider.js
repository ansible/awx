export default function($stateProvider) {
    this.$get = function() {
        return {
            addSocket: function(state){
                // The login route has a 'null' socket because it should
                // neither subscribe or unsubscribe
                if(state.socket!==null){
                    if(!state.resolve){
                        state.resolve = {};
                    }
                    state.resolve.socket = ['SocketService', '$stateParams',
                        function(SocketService, $stateParams) {
                            SocketService.addStateResolve(state, $stateParams.id);
                        }
                    ];
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
