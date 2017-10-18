export default function($stateProvider) {
    this.$get = function() {
        return {
            // attaches socket as resolvable if specified in state definition
            addSocket: function(state){
                // The login route has a 'null' socket because it should
                // neither subscribe or unsubscribe
                if(state.data && state.data.socket!==null){
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
            // builds a state definition with default slaw
            buildDefinition: function(state) {
                let params, defaults, definition,
                    searchPrefix = state.searchPrefix ? `${state.searchPrefix}_search` : null,
                    route = state.route || state.url;

                if (searchPrefix) {
                    defaults = {
                        params: {
                            [searchPrefix]: {
                                value: {
                                    page_size: "20",
                                    order_by: "name"
                                },
                                dynamic: true,
                                squash: false
                            }
                        }
                    };
                    route = !state.squashSearchUrl ? `${route}?{${searchPrefix}:queryset}` : route;
                    params = state.params === undefined ? defaults.params : _.merge(defaults.params, state.params);
                } else {
                    params = state.params;
                }

                definition = {
                    name: state.name,
                    url: route,
                    abstract: state.abstract,
                    controller: state.controller,
                    templateUrl: state.templateUrl,
                    templateProvider: state.templateProvider,
                    resolve: state.resolve,
                    params: params,
                    data: state.data,
                    ncyBreadcrumb: state.ncyBreadcrumb,
                    onEnter: state.onEnter,
                    onExit: state.onExit,
                    template: state.template,
                    controllerAs: state.controllerAs,
                    views: state.views,
                    parent: state.parent,
                    redirectTo: state.redirectTo,
                    // new in uiRouter 1.0
                    lazyLoad: state.lazyLoad,
                };
                this.addSocket(definition);
                return definition;
            },
            // registers a state definition with $stateProvider service
            addState: function(state) {
                let definition = this.buildDefinition(state);
                $stateProvider.state(state.name, definition);
            }
        };
    };
}
