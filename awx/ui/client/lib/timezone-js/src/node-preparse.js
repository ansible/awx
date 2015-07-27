(function () {

  var fs = require('fs')
  , timezoneJS = require('./date')
  , EXCLUDED = new RegExp('Makefile|factory|(\\.+)', 'i');

  function parse(args) {
    // Upgrade passed script args to real Array
    if (args.length < 3) {
      console.log('Usage: node node-preparse.js zoneFileDirectory [exemplarCities] > outputfile.json');
      console.log('Ex. >>> node node-preparse.js olson_files "Asia/Tokyo, America/New_York, Europe/London" > major_cities.json');
      console.log('Ex. >>> node node-preparse.js olson_files > all_cities.json');
      return;
    }
    var baseDir = args[2]
    , cities = args[3]
    , result = {}
    , _tz = timezoneJS.timezone;

    _tz.loadingScheme = _tz.loadingSchemes.MANUAL_LOAD;
    _tz.zoneFiles = fs.readdirSync(baseDir);

    for (var i = 0; i < _tz.zoneFiles.length; i++) {
      var zoneFile = _tz.zoneFiles[i];
      if (EXCLUDED.test(zoneFile)) continue;
      var zoneData = fs.readFileSync(baseDir + '/' + zoneFile, 'utf8');
      _tz.parseZones(zoneData);
    }
    if (cities) {
      cities = cities.replace(/ /g, '').split(',');
      var zones = {};
      var rules = {};
      for (var i = 0; i < cities.length; i++) {
        var city = cities[i];
        zones[city] = _tz.zones[city];
      }
      for (var n in zones) {
        var zList = zones[n];
        for (var i = 0; i < zList.length; i++) {
          var ruleKey = zList[i][1];
          rules[ruleKey] = _tz.rules[ruleKey];
        }
      }
      result.zones = zones;
      result.rules = rules;
    }
    else {
      result.zones = _tz.zones;
      result.rules = _tz.rules;
    }
    console.log(JSON.stringify(result));
  }

  module.exports = parse(process.argv);

}).call(this);
