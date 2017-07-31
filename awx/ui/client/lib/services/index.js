import CacheService from './cache.service';
import EventService from './event.service';
import PathService from './path.service';
import BaseStringService from './base-string.service';
import AppStrings from './app.strings';

angular
    .module('at.lib.services', [])
    .service('AppStrings', AppStrings)
    .service('BaseStringService', BaseStringService)
    .service('CacheService', CacheService)
    .service('EventService', EventService)
    .service('PathService', PathService);
