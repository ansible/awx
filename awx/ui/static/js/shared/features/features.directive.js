import featureController from 'tower/shared/features/features.controller';
export default [  function() {
    return {
        restrict: 'A',
        controller: featureController,
        link: function (scope, element, attrs, controller){
            if(attrs.awFeature.length > 0){
                if(!controller.isFeatureEnabled(attrs.awFeature)){
                    element.remove();
                }
            }
        }

    };
}];
