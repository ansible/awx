
function readText(uri){
  var jf = new java.io.File(uri);
  var sb = new java.lang.StringBuffer();
  var input = new java.io.BufferedReader(new java.io.FileReader(jf));
  var line = "";
  var str = "";
  while((line = input.readLine()) != null){
    sb.append(line);
    sb.append(java.lang.System.getProperty("line.separator"));
  }
  // Cast to real JS String
  str += sb.toString();
  return str;
}

function main(args) {
  // Upgrade passed script args to real Array
  if (!args.length) {
    print('Usage: rhino preparse.js zoneFileDirectory [exemplarCities] > outputfile.json');
    print('Ex. >>> rhino preparse.js olson_files "Asia/Tokyo, America/New_York, Europe/London" > major_cities.json');
    print('Ex. >>> rhino preparse.js olson_files > all_cities.json');
    return;
  }
  var baseDir = args[0];
  var cities = args[1];
  load('date.js');
  load('../../src/json.js');
  var _tz = fleegix.date.timezone;
  _tz.loadingScheme = _tz.loadingSchemes.MANUAL_LOAD;
  for (var i = 0; i < _tz.zoneFiles.length; i++) {
    var zoneFile = _tz.zoneFiles[i];
    var zoneData = readText(baseDir + '/' + zoneFile);
    _tz.parseZones(zoneData);
  }
  var result = {};
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
    result.rules = _tz.rules
  }
  result = fleegix.json.serialize(result);
  print(result);
}

main(arguments);


