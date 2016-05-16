export default function($stateProvider) {
    this.$get = function() {
        return {
            getResolves: function(state){
                var resolve = state.resolve || {},
                routes = ["signIn", "signOut"];
                if(_.indexOf(routes, state.name)>-1){
                    return;
                }
                else{
                    resolve.features = ['FeaturesService', function(FeaturesService) {
                            return FeaturesService.get();
                        }];
                    // resolve.features = ['CheckLicense', 'Store', '$state',
                    //     function(CheckLicense, Store, $state) {
                    //         var license = Store('license');
                    //         if(CheckLicense.valid(license)=== false){
                    //             $state.go('license');
                    //         }
                    //     }];
                    return resolve;
                }
            },

            addState: function(state) {
                var route = state.route || state.url,
                resolve = this.getResolves(state);

                $stateProvider.state(state.name, {
                    url: route,
                    controller: state.controller,
                    templateUrl: state.templateUrl,
                    resolve: resolve,
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
