
export default function($stateProvider){
    this.$get = function(){
        return {
            addState: function(state) {
                $stateProvider.state(state.name , {
                    url: state.route,
                    controller: state.controller,
                    templateUrl: state.templateUrl,
                    resolve: state.resolve
                });
            }
        };
    };
}
