import AppStrings from '~services/app.strings';
import BaseStringService from '~services/base-string.service';
import CacheService from '~services/cache.service';
import EventService from '~services/event.service';

const MODULE_NAME = 'at.lib.services';

angular
    .module(MODULE_NAME, [
        'I18N'
    ])
    .service('AppStrings', AppStrings)
    .service('BaseStringService', BaseStringService)
    .service('CacheService', CacheService)
    .service('EventService', EventService);

export default MODULE_NAME;
