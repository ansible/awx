export default [function() {
    return {
        restrict: 'E',
        scope: {
            maxPanels: '@',
            panelContainer: '@'
        },
        link: function(scope) {

            const maxPanels = parseInt(scope.maxPanels);

            scope.$watch(
                () => angular.element('#' + scope.panelContainer).find('.at-Panel').length,
                () => {
                    const panels = angular.element('#' + scope.panelContainer).find('.at-Panel');
                    if(panels.length > maxPanels) {
                        // hide the excess panels
                        $(panels).each(function( index ) {
                            if(index+1 > maxPanels) {
                                $(this).addClass('d-none');
                            }
                            else {
                                $(this).removeClass('d-none');
                            }
                        });
                    } else {
                        // show all the panels
                        $(panels).removeClass('d-none');
                    }
                }
            );
        }
    };
}];
