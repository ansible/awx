import IndexController from './index.controller';

function routes ($stateProvider) {
    $stateProvider.state({
        name: 'credentials',
        url: '/credentials',
        templateUrl: '/static/views/credentials/index.view.html',
        controller: IndexController,
        controllerAs: 'vm'
    });
}

routes.$inject = [
  '$stateProvider'
];

angular.module('at.feature.credentials', []).config(routes);
