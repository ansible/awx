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
                () => angular.element('#' + scope.panelContainer).find('.Panel').length,
                () => {
                    const panels = angular.element('#' + scope.panelContainer).find('.Panel');
                    if(panels.length > maxPanels) {
                        // hide the excess panels
                        $(panels).each(function( index ) {
                            if(index+1 > maxPanels) {
                                $(this).addClass('Panel-hidden');
                            }
                            else {
                                $(this).removeClass('Panel-hidden');
                            }
                        });
                    } else {
                        // show all the panels
                        $(panels).removeClass('Panel-hidden');
                    }
                }
            );
        }
    };
}];
