import controller from './multi-select-list.controller';

export default
    [   function() {
        return {
            restrict: 'A',
            scope: {
            },
            controller: controller
        };
    }];
