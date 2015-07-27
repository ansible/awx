var fs = require('fs');
(function () {
  var root = this;

  var TestUtils = {};
  if (typeof exports !== 'undefined') {
    TestUtils = exports;
  } else {
    TestUtils = root.TestUtils = {};
  }

  var init = function (timezoneJS, options) {
    var opts = {
      async: false,
      loadingScheme: timezoneJS.timezone.loadingSchemes.LAZY_LOAD
    };
    for (var k in (options || {})) {
      opts[k] = options[k];
    }
    
    timezoneJS.timezone.transport = function (opts) {
      // No success handler, what's the point?
      if (opts.async) {
        if (typeof opts.success !== 'function') return;
        opts.error = opts.error || console.error;
        return fs.readFile(opts.url, 'utf8', function (err, data) {
          return err ? opts.error(err) : opts.success(data);
        });
      }
      return fs.readFileSync(opts.url, 'utf8');
    };

    timezoneJS.timezone.loadingScheme = opts.loadingScheme;
    if (opts.loadingScheme !== timezoneJS.timezone.loadingSchemes.MANUAL_LOAD) {
      //Set up again
      timezoneJS.timezone.zoneFileBasePath = 'lib/tz';
      timezoneJS.timezone.init(opts);
    }
    
    return timezoneJS;
  };

  TestUtils.getTimezoneJS = function (options) {
    //Delete date.js from require cache to force it to reload
    for (var k in require.cache) {
      if (k.indexOf('date.js') > -1) {
        delete require.cache[k];
      }
    }
    return init(require('../src/date'), options);
  }

  TestUtils.parseISO = function (timestring) {
    var pat = '^(?:([+-]?[0-9]{4,})(?:-([0-9]{2})(?:-([0-9]{2}))?)?)?' +
      '(?:T(?:([0-9]{2})(?::([0-9]{2})(?::([0-9]{2})(?:\\.' +
      '([0-9]{3}))?)?)?)?(Z|[-+][0-9]{2}:[0-9]{2})?)?$';
    var match = timestring.match(pat);
    if (match) {
      var parts = {
        year: match[1] || 0,
        month:  match[2] || 1,
        day:  match[3] || 1,
        hour:  match[4] || 0,
        minute:  match[5] || 0,
        second:  match[6] || 0,
        milli:  match[7] || 0,
        offset:  match[8] || "Z"
      };

      var utcDate = Date.UTC(parts.year, parts.month-1, parts.day,
        parts.hour, parts.minute, parts.second, parts.milli);

      if (parts.offset !== "Z") {
        match = parts.offset.match('([-+][0-9]{2})(?::([0-9]{2}))?');
        if (!match) {
          return NaN;
        }
        var offset = match[1]*60*60*1000+(match[2] || 0)*60*1000;
        utcDate -= offset;
      }
      return new Date(utcDate);
    }
    return null;
  };
}).call(this);
