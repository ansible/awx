const templateUrl = require('~components/dialog/dialog.partial.html');

export default {
    templateUrl,
    controllerAs: 'vm',
    transclude: true,
    bindings: {
        title: '=',
        onClose: '=',
    },
};
