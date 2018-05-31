import AppStrings from '~services/app.strings';
import BaseStringService from '~services/base-string.service';
import CacheService from '~services/cache.service';
import EventService from '~services/event.service';
import TagService from '~services/tag.service';

const MODULE_NAME = 'at.lib.services';

angular
    .module(MODULE_NAME, [
        'I18N'
    ])
    .service('AppStrings', AppStrings)
    .service('BaseStringService', BaseStringService)
    .service('CacheService', CacheService)
    .service('EventService', EventService)
    .service('TagService', TagService);

export default MODULE_NAME;
