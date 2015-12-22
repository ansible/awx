
export default angular.module('uiRouterHelper',[

    ])

    .provider('$stateExtender', function($stateProvider){
        this.$get = function($state){
            return {
                addState: function(state) {
                    $stateProvider.state(state.name , {
                        url: state.route,
                        controller: state.controller,
                        templateUrl: state.templateUrl,
                        resolve: state.resolve
                    });


                }
            }
        }
    });
