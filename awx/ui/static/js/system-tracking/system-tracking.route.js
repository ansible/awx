import controller from './system-tracking.controller';

export default {
    route: '/inventories/:id/system-tracking/:filters',
    controller: controller,
    templateUrl: '/static/js/system-tracking/system-tracking.partial.html'
};
