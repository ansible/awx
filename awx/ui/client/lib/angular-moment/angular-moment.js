/* angular-moment.js / v0.10.1 / (c) 2013, 2014, 2015 Uri Shaked / MIT Licence */

'format amd';
/* global define */

(function () {
	'use strict';

	function angularMoment(angular, moment) {

		/**
		 * @ngdoc overview
		 * @name angularMoment
		 *
		 * @description
		 * angularMoment module provides moment.js functionality for angular.js apps.
		 */
		return angular.module('angularMoment', [])

		/**
		 * @ngdoc object
		 * @name angularMoment.config:angularMomentConfig
		 *
		 * @description
		 * Common configuration of the angularMoment module
		 */
			.constant('angularMomentConfig', {
				/**
				 * @ngdoc property
				 * @name angularMoment.config.angularMomentConfig#preprocess
				 * @propertyOf angularMoment.config:angularMomentConfig
				 * @returns {string} The default preprocessor to apply
				 *
				 * @description
				 * Defines a default preprocessor to apply (e.g. 'unix', 'etc', ...). The default value is null,
				 * i.e. no preprocessor will be applied.
				 */
				preprocess: null, // e.g. 'unix', 'utc', ...

				/**
				 * @ngdoc property
				 * @name angularMoment.config.angularMomentConfig#timezone
				 * @propertyOf angularMoment.config:angularMomentConfig
				 * @returns {string} The default timezone
				 *
				 * @description
				 * The default timezone (e.g. 'Europe/London'). Empty string by default (does not apply
				 * any timezone shift).
				 */
				timezone: '',

				/**
				 * @ngdoc property
				 * @name angularMoment.config.angularMomentConfig#format
				 * @propertyOf angularMoment.config:angularMomentConfig
				 * @returns {string} The pre-conversion format of the date
				 *
				 * @description
				 * Specify the format of the input date. Essentially it's a
				 * default and saves you from specifying a format in every
				 * element. Overridden by element attr. Null by default.
				 */
				format: null,

				/**
				 * @ngdoc property
				 * @name angularMoment.config.angularMomentConfig#statefulFilters
				 * @propertyOf angularMoment.config:angularMomentConfig
				 * @returns {boolean} Whether angular-moment filters should be stateless (or not)
				 *
				 * @description
				 * Specifies whether the filters included with angular-moment are stateful.
				 * Stateful filters will automatically re-evaluate whenever you change the timezone
				 * or language settings, but may negatively impact performance. true by default.
				 */
				statefulFilters: true
			})

		/**
		 * @ngdoc object
		 * @name angularMoment.object:moment
		 *
		 * @description
		 * moment global (as provided by the moment.js library)
		 */
			.constant('moment', moment)

		/**
		 * @ngdoc object
		 * @name angularMoment.config:amTimeAgoConfig
		 * @module angularMoment
		 *
		 * @description
		 * configuration specific to the amTimeAgo directive
		 */
			.constant('amTimeAgoConfig', {
				/**
				 * @ngdoc property
				 * @name angularMoment.config.amTimeAgoConfig#withoutSuffix
				 * @propertyOf angularMoment.config:amTimeAgoConfig
				 * @returns {boolean} Whether to include a suffix in am-time-ago directive
				 *
				 * @description
				 * Defaults to false.
				 */
				withoutSuffix: false,

				/**
				 * @ngdoc property
				 * @name angularMoment.config.amTimeAgoConfig#serverTime
				 * @propertyOf angularMoment.config:amTimeAgoConfig
				 * @returns {number} Server time in milliseconds since the epoch
				 *
				 * @description
				 * If set, time ago will be calculated relative to the given value.
				 * If null, local time will be used. Defaults to null.
				 */
				serverTime: null,

				/**
				 * @ngdoc property
				 * @name angularMoment.config.amTimeAgoConfig#titleFormat
				 * @propertyOf angularMoment.config:amTimeAgoConfig
				 * @returns {string} The format of the date to be displayed in the title of the element. If null,
				 *        the directive set the title of the element.
				 *
				 * @description
				 * The format of the date used for the title of the element. null by default.
				 */
				titleFormat: null,

				/**
				 * @ngdoc property
				 * @name angularMoment.config.amTimeAgoConfig#fullDateThreshold
				 * @propertyOf angularMoment.config:amTimeAgoConfig
				 * @returns {number} The minimum number of days for showing a full date instead of relative time
				 *
				 * @description
				 * The threshold for displaying a full date. The default is null, which means the date will always
				 * be relative, and full date will never be displayed.
				 */
				fullDateThreshold: null,

				/**
				 * @ngdoc property
				 * @name angularMoment.config.amTimeAgoConfig#fullDateFormat
				 * @propertyOf angularMoment.config:amTimeAgoConfig
				 * @returns {string} The format to use when displaying a full date.
				 *
				 * @description
				 * Specify the format of the date when displayed as full date. null by default.
				 */
				fullDateFormat: null
			})

		/**
		 * @ngdoc directive
		 * @name angularMoment.directive:amTimeAgo
		 * @module angularMoment
		 *
		 * @restrict A
		 */
			.directive('amTimeAgo', ['$window', 'moment', 'amMoment', 'amTimeAgoConfig', 'angularMomentConfig', function ($window, moment, amMoment, amTimeAgoConfig, angularMomentConfig) {

				return function (scope, element, attr) {
					var activeTimeout = null;
					var currentValue;
					var currentFormat = angularMomentConfig.format;
					var withoutSuffix = amTimeAgoConfig.withoutSuffix;
					var titleFormat = amTimeAgoConfig.titleFormat;
					var fullDateThreshold = amTimeAgoConfig.fullDateThreshold;
					var fullDateFormat = amTimeAgoConfig.fullDateFormat;
					var localDate = new Date().getTime();
					var preprocess = angularMomentConfig.preprocess;
					var modelName = attr.amTimeAgo;
					var isTimeElement = ('TIME' === element[0].nodeName.toUpperCase());

					function getNow() {
						var now;
						if (amTimeAgoConfig.serverTime) {
							var localNow = new Date().getTime();
							var nowMillis = localNow - localDate + amTimeAgoConfig.serverTime;
							now = moment(nowMillis);
						}
						else {
							now = moment();
						}
						return now;
					}

					function cancelTimer() {
						if (activeTimeout) {
							$window.clearTimeout(activeTimeout);
							activeTimeout = null;
						}
					}

					function updateTime(momentInstance) {
						var daysAgo = getNow().diff(momentInstance, 'day');
						var showFullDate = fullDateThreshold && daysAgo >= fullDateThreshold;

						if (showFullDate) {
							element.text(momentInstance.format(fullDateFormat));
						} else {
							element.text(momentInstance.from(getNow(), withoutSuffix));
						}

						if (titleFormat && !element.attr('title')) {
							element.attr('title', momentInstance.local().format(titleFormat));
						}

						if (!showFullDate) {
							var howOld = Math.abs(getNow().diff(momentInstance, 'minute'));
							var secondsUntilUpdate = 3600;
							if (howOld < 1) {
								secondsUntilUpdate = 1;
							} else if (howOld < 60) {
								secondsUntilUpdate = 30;
							} else if (howOld < 180) {
								secondsUntilUpdate = 300;
							}

							activeTimeout = $window.setTimeout(function () {
								updateTime(momentInstance);
							}, secondsUntilUpdate * 1000);
						}
					}

					function updateDateTimeAttr(value) {
						if (isTimeElement) {
							element.attr('datetime', value);
						}
					}

					function updateMoment() {
						cancelTimer();
						if (currentValue) {
							var momentValue = amMoment.preprocessDate(currentValue, preprocess, currentFormat);
							updateTime(momentValue);
							updateDateTimeAttr(momentValue.toISOString());
						}
					}

					scope.$watch(modelName, function (value) {
						if ((typeof value === 'undefined') || (value === null) || (value === '')) {
							cancelTimer();
							if (currentValue) {
								element.text('');
								updateDateTimeAttr('');
								currentValue = null;
							}
							return;
						}

						currentValue = value;
						updateMoment();
					});

					if (angular.isDefined(attr.amWithoutSuffix)) {
						scope.$watch(attr.amWithoutSuffix, function (value) {
							if (typeof value === 'boolean') {
								withoutSuffix = value;
								updateMoment();
							} else {
								withoutSuffix = amTimeAgoConfig.withoutSuffix;
							}
						});
					}

					attr.$observe('amFormat', function (format) {
						if (typeof format !== 'undefined') {
							currentFormat = format;
							updateMoment();
						}
					});

					attr.$observe('amPreprocess', function (newValue) {
						preprocess = newValue;
						updateMoment();
					});

					attr.$observe('amFullDateThreshold', function (newValue) {
						fullDateThreshold = newValue;
						updateMoment();
					});

					attr.$observe('amFullDateFormat', function (newValue) {
						fullDateFormat = newValue;
						updateMoment();
					});

					scope.$on('$destroy', function () {
						cancelTimer();
					});

					scope.$on('amMoment:localeChanged', function () {
						updateMoment();
					});
				};
			}])

		/**
		 * @ngdoc service
		 * @name angularMoment.service.amMoment
		 * @module angularMoment
		 */
			.service('amMoment', ['moment', '$rootScope', '$log', 'angularMomentConfig', function (moment, $rootScope, $log, angularMomentConfig) {
				/**
				 * @ngdoc property
				 * @name angularMoment:amMoment#preprocessors
				 * @module angularMoment
				 *
				 * @description
				 * Defines the preprocessors for the preprocessDate method. By default, the following preprocessors
				 * are defined: utc, unix.
				 */
				this.preprocessors = {
					utc: moment.utc,
					unix: moment.unix
				};

				/**
				 * @ngdoc function
				 * @name angularMoment.service.amMoment#changeLocale
				 * @methodOf angularMoment.service.amMoment
				 *
				 * @description
				 * Changes the locale for moment.js and updates all the am-time-ago directive instances
				 * with the new locale. Also broadcasts an `amMoment:localeChanged` event on $rootScope.
				 *
				 * @param {string} locale Locale code (e.g. en, es, ru, pt-br, etc.)
				 * @param {object} customization object of locale strings to override
				 */
				this.changeLocale = function (locale, customization) {
					var result = moment.locale(locale, customization);
					if (angular.isDefined(locale)) {
						$rootScope.$broadcast('amMoment:localeChanged');

					}
					return result;
				};

				/**
				 * @ngdoc function
				 * @name angularMoment.service.amMoment#changeTimezone
				 * @methodOf angularMoment.service.amMoment
				 *
				 * @description
				 * Changes the default timezone for amCalendar, amDateFormat and amTimeAgo. Also broadcasts an
				 * `amMoment:timezoneChanged` event on $rootScope.
				 *
				 * @param {string} timezone Timezone name (e.g. UTC)
				 */
				this.changeTimezone = function (timezone) {
					angularMomentConfig.timezone = timezone;
					$rootScope.$broadcast('amMoment:timezoneChanged');
				};

				/**
				 * @ngdoc function
				 * @name angularMoment.service.amMoment#preprocessDate
				 * @methodOf angularMoment.service.amMoment
				 *
				 * @description
				 * Preprocess a given value and convert it into a Moment instance appropriate for use in the
				 * am-time-ago directive and the filters.
				 *
				 * @param {*} value The value to be preprocessed
				 * @param {string} preprocess The name of the preprocessor the apply (e.g. utc, unix)
				 * @param {string=} format Specifies how to parse the value (see {@link http://momentjs.com/docs/#/parsing/string-format/})
				 * @return {Moment} A value that can be parsed by the moment library
				 */
				this.preprocessDate = function (value, preprocess, format) {
					if (angular.isUndefined(preprocess)) {
						preprocess = angularMomentConfig.preprocess;
					}
					if (this.preprocessors[preprocess]) {
						return this.preprocessors[preprocess](value, format);
					}
					if (preprocess) {
						$log.warn('angular-moment: Ignoring unsupported value for preprocess: ' + preprocess);
					}
					if (!isNaN(parseFloat(value)) && isFinite(value)) {
						// Milliseconds since the epoch
						return moment(parseInt(value, 10));
					}
					// else just returns the value as-is.
					return moment(value, format);
				};

				/**
				 * @ngdoc function
				 * @name angularMoment.service.amMoment#applyTimezone
				 * @methodOf angularMoment.service.amMoment
				 *
				 * @description
				 * Apply a timezone onto a given moment object - if moment-timezone.js is included
				 * Otherwise, it'll not apply any timezone shift.
				 *
				 * @param {Moment} aMoment a moment() instance to apply the timezone shift to
				 * @param {string=} timezone The timezone to apply. If none given, will apply the timezone
				 * 		configured in angularMomentConfig.timezone.
				 *
				 * @returns {Moment} The given moment with the timezone shift applied
				 */
				this.applyTimezone = function (aMoment, timezone) {
					timezone = timezone || angularMomentConfig.timezone;
					if (aMoment && timezone) {
						if (aMoment.tz) {
							aMoment = aMoment.tz(timezone);
						} else {
							$log.warn('angular-moment: timezone specified but moment.tz() is undefined. Did you forget to include moment-timezone.js?');
						}
					}
					return aMoment;
				};
			}])

		/**
		 * @ngdoc filter
		 * @name angularMoment.filter:amCalendar
		 * @module angularMoment
		 */
			.filter('amCalendar', ['moment', 'amMoment', 'angularMomentConfig', function (moment, amMoment, angularMomentConfig) {
				function amCalendarFilter(value, preprocess) {
					if (typeof value === 'undefined' || value === null) {
						return '';
					}

					value = amMoment.preprocessDate(value, preprocess);
					var date = moment(value);
					if (!date.isValid()) {
						return '';
					}

					return amMoment.applyTimezone(date).calendar();
				}

				// Since AngularJS 1.3, filters have to explicitly define being stateful
				// (this is no longer the default).
				amCalendarFilter.$stateful = angularMomentConfig.statefulFilters;

				return amCalendarFilter;
			}])

		/**
		 * @ngdoc filter
		 * @name angularMoment.filter:amDifference
		 * @module angularMoment
		 */
			.filter('amDifference', ['moment', 'amMoment', 'angularMomentConfig', function (moment, amMoment, angularMomentConfig) {
				function amDifferenceFilter(value, otherValue, unit, usePrecision, preprocessValue, preprocessOtherValue) {
					if (typeof value === 'undefined' || value === null) {
						return '';
					}

					value = amMoment.preprocessDate(value, preprocessValue);
					var date = moment(value);
					if (!date.isValid()) {
						return '';
					}

					var date2;
					if (typeof otherValue === 'undefined' || otherValue === null) {
						date2 = moment();
					} else {
						otherValue = amMoment.preprocessDate(otherValue, preprocessOtherValue);
						date2 = moment(otherValue);
						if (!date2.isValid()) {
							return '';
						}
					}

					return amMoment.applyTimezone(date).diff(amMoment.applyTimezone(date2), unit, usePrecision);
				}

				amDifferenceFilter.$stateful = angularMomentConfig.statefulFilters;

				return amDifferenceFilter;
			}])

		/**
		 * @ngdoc filter
		 * @name angularMoment.filter:amDateFormat
		 * @module angularMoment
		 * @function
		 */
			.filter('amDateFormat', ['moment', 'amMoment', 'angularMomentConfig', function (moment, amMoment, angularMomentConfig) {
				function amDateFormatFilter(value, format, preprocess, timezone) {
					if (typeof value === 'undefined' || value === null) {
						return '';
					}

					value = amMoment.preprocessDate(value, preprocess);
					var date = moment(value);
					if (!date.isValid()) {
						return '';
					}

					return amMoment.applyTimezone(date, timezone).format(format);
				}

				amDateFormatFilter.$stateful = angularMomentConfig.statefulFilters;

				return amDateFormatFilter;
			}])

		/**
		 * @ngdoc filter
		 * @name angularMoment.filter:amDurationFormat
		 * @module angularMoment
		 * @function
		 */
			.filter('amDurationFormat', ['moment', 'angularMomentConfig', function (moment, angularMomentConfig) {
				function amDurationFormatFilter(value, format, suffix) {
					if (typeof value === 'undefined' || value === null) {
						return '';
					}

					return moment.duration(value, format).humanize(suffix);
				}

				amDurationFormatFilter.$stateful = angularMomentConfig.statefulFilters;

				return amDurationFormatFilter;
			}])

		/**
		 * @ngdoc filter
		 * @name angularMoment.filter:amTimeAgo
		 * @module angularMoment
		 * @function
		 */
			.filter('amTimeAgo', ['moment', 'amMoment', 'angularMomentConfig', function (moment, amMoment, angularMomentConfig) {
				function amTimeAgoFilter(value, preprocess, suffix) {
					if (typeof value === 'undefined' || value === null) {
						return '';
					}

					value = amMoment.preprocessDate(value, preprocess);
					var date = moment(value);
					if (!date.isValid()) {
						return '';
					}

					return amMoment.applyTimezone(date).fromNow(suffix);
				}

				amTimeAgoFilter.$stateful = angularMomentConfig.statefulFilters;

				return amTimeAgoFilter;
			}]);
	}

	if (typeof define === 'function' && define.amd) {
		define(['angular', 'moment'], angularMoment);
	} else if (typeof module !== 'undefined' && module && module.exports) {
		angularMoment(angular, require('moment'));
		module.exports = 'angularMoment';
	} else {
		angularMoment(angular, window.moment);
	}
})();
