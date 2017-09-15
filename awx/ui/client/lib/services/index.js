import CacheService from '~services/cache.service';
import EventService from '~services/event.service';
import BaseStringService from '~services/base-string.service';
import AppStrings from '~services/app.strings';

angular
    .module('at.lib.services', [])
    .service('AppStrings', AppStrings)
    .service('BaseStringService', BaseStringService)
    .service('CacheService', CacheService)
    .service('EventService', EventService);
