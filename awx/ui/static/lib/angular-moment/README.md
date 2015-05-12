angular-moment
==============

AngularJS directive and filters for [Moment.JS](http://www.momentjs.com).

Copyright (C) 2013, 2014, 2015, Uri Shaked <uri@urish.org>

[![Build Status](https://travis-ci.org/urish/angular-moment.png?branch=master)](https://travis-ci.org/urish/angular-moment)
[![Coverage Status](https://coveralls.io/repos/urish/angular-moment/badge.png)](https://coveralls.io/r/urish/angular-moment)

Installation
------------

You can choose your preferred method of installation:
* Through bower: `bower install angular-moment --save`
* Through npm: `npm install angular-moment --save`
* Through NuGet: `Install-Package angular-moment`
* From a CDN: [jsDelivr](https://cdn.jsdelivr.net/angular.moment/0.10.1/angular-moment.min.js) or [CDNJS](https://cdnjs.cloudflare.com/ajax/libs/angular-moment/0.10.1/angular-moment.min.js)
* Download from github: [angular-moment.min.js](https://raw.github.com/urish/angular-moment/master/angular-moment.min.js)

Usage
-----
Include both moment.js and angular-moment.js in your application.

```html
<script src="components/moment/moment.js"></script>
<script src="components/angular-moment/angular-moment.js"></script>
```

Add the module `angularMoment` as a dependency to your app module:

```js
var myapp = angular.module('myapp', ['angularMoment']);
```

If you need internationalization support, load specified moment.js locale file first:

```html
<script src="components/moment/locale/de.js"></script>
```

Then call the `amMoment.changeLocale()` method (e.g. inside your app's run() callback):

```js
myapp.run(function(amMoment) {
	amMoment.changeLocale('de');
});
```

### Configuration

Parameter `preprocess`(e.g: `unix`, `utc`) would pre-execute before.

```js
angular.module('myapp').constant('angularMomentConfig', {
	preprocess: 'unix', // optional
	timezone: 'Europe/London' // optional
});
```

### Timeago directive
Use am-time-ago directive to format your relative timestamps. For example:

```html
<span am-time-ago="message.time"></span>
<span am-time-ago="message.time" am-preprocess="unix"></span>
```

angular-moment will dynamically update the span to indicate how much time
passed since the message was created. So, if your controller contains the following
code:
```js
$scope.message = {
   text: 'hello world!',
   time: new Date()
};
```

The user will initially see "a few seconds ago", and about a minute
after the span will automatically update with the text "a minute ago",
etc.

### amDateFormat filter
Format dates using moment.js format() method. Example:

```html
<span>{{message.time | amDateFormat:'dddd, MMMM Do YYYY, h:mm:ss a'}}</span>
```

This snippet will format the given time as "Monday, October 7th 2013, 12:36:29 am".

For more information about Moment.JS formatting options, see the
[docs for the format() function](http://momentjs.com/docs/#/displaying/format/).

### amCalendar filter

Format dates using moment.js calendar() method. Example:

```html
<span>{{message.time | amCalendar}}</span>
```

This snippet will format the given time as e.g. "Today 2:30 AM" or "Last Monday 2:30 AM" etc..

For more information about Moment.JS calendar time format, see the
[docs for the calendar() function](http://momentjs.com/docs/#/displaying/calendar-time/).

### amDifference filter

Get the difference between two dates in milliseconds.
Parameters are date, units and usePrecision. Date defaults to current date. Example:

```html
<span>Scheduled {{message.createdAt | amDifference : null : 'days' }} days from now</span>
```

This snippet will return the number of days between the current date and the date filtered.

For more information about Moment.JS difference function, see the
[docs for the diff() function](http://momentjs.com/docs/#/displaying/difference/).

### Time zone support

The `amDateFormat` and `amCalendar` filters can be configured to display dates aligned
to a specific timezone. You can configure the timezone using the following syntax:

```js
angular.module('myapp').constant('angularMomentConfig', {
    timezone: 'Name of Timezone' // e.g. 'Europe/London'
});
```

Remember to include `moment-timezone.js` in your project, otherwise the custom timezone
functionality will not be available. You will also need to include a timezone data file that
you can create using the [Timezone Data Builder](http://momentjs.com/timezone/data/)
or simply download from [here](https://rawgithub.com/qw4n7y/7282780/raw/6ae3b334b295f93047e8f3ad300db6bc4387e235/moment-timezone-data.js).

License
----

Released under the terms of the [MIT License](LICENSE).
