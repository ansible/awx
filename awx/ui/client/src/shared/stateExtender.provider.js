
export default function($stateProvider){
    this.$get = function(){
        return {
            addState: function(state) {
                var route = state.route || state.url;
                $stateProvider.state(state.name , {
                    url: route,
                    controller: state.controller,
                    templateUrl: state.templateUrl,
                    resolve: state.resolve,
                    params: state.params,
                    data: state.data,
                    ncyBreadcrumb: state.ncyBreadcrumb
                });
            }
        };
    };
}
