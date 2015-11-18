angular-filters [![Build Status](https://travis-ci.org/frapontillo/angular-filters.png?branch=master)](https://travis-ci.org/frapontillo/angular-filters)
===============

A collection of useful filters for [AngularJS](http://angularjs.org/).

You can install the latest version of `angular-filters` with `bower`:

```bash
$ bower install angular-filters
```

Then, simply include `./dist/angular-filters.js` or `./dist/angular-filters.min.js` in your Web app and inject the module `frapontillo.ex.filters` in your application.

## Filters specs

The included filters are:

- [`bool:trueValue:falseValue`](#bool)
- [`default:defaultValue`](#default)
- [`firstNotNull`](#firstnotnull)
- [`lastNotNull`](#lastnotnull)
- [`max`](#max)
- [`min`](#min)
- [`property`](#property)
- [`join`](#join)

### bool

The `bool` filter allows to **specify true and false values** to show depending on the input value. The second parameter will be returned if and only if the first parameter is `true`; the third parameter will be returned if and only if the first parameter is `false`.

This filter can be used to print a specific message depending on a boolean value.

Use it as follows:

```html
	<p>{{ someBoolValue | bool:'Candies!':'No candies :(' }}</p>
```

```javascript
	$scope.returnValue = $filter('bool')($scope.someBoolValue, 'Candies!', 'No candies :(');
```

### default

The `default` filter allows to **specify a default fallback value** if an object is one of the following:

- `null`
- `undefined`
- empty string, `''`
- `NaN`

Please notice that if a value equals to `0`, the default value won't be returned, as `0` is accepted.

This filter is useful when another filter return is not safe and when you want to display a fallback value.

Use it as follows:

```html
	<p>{{ someValue | number:2 | default:'No value is available.' }}</p>
```

```javascript
	$scope.returnValue = $filter('default')
		($filter('number')($scope.someValue, 2), 'No value is available.');
```

### firstNotNull

The `firstNotNull` filter returns the **first element from an array** that is neither `null` or `undefined`. This means it returns all numbers and strings, even if empty. It returns `undefined` if all values aren't set or if the array is empty.

Use it as follows:

```html
	<p>{{ myValues | firstNotNull }}</p>
```

```javascript
	$scope.firstValue = $filter('firstNotNull')($scope.myValues);
```

### lastNotNull

The `lastNotNull` filter returns the **last element from an array** that is neither `null` or `undefined`. This means it returns all numbers and strings, even if empty. It returns `undefined` if all values aren't set or if the array is empty.

Use it as follows:

```html
	<p>{{ myValues | lastNotNull }}</p>
```

```javascript
	$scope.firstValue = $filter('lastNotNull')($scope.myValues);
```

### max

The `max` filter returns the **maximum value from an array** that is neither `null` or `undefined`. It returns `undefined` if all values aren't set or if the array is empty.

Use it as follows:

```html
	<p>{{ myValues | max }}</p>
```

```javascript
	$scope.maxValue = $filter('max')($scope.myValues);
```

### min

The `min` filter returns the **minimum value from an array** that is neither `null` or `undefined`. It returns `undefined` if all values aren't set or if the array is empty.

Use it as follows:

```html
	<p>{{ myValues | min }}</p>
```

```javascript
	$scope.minValue = $filter('min')($scope.myValues);
```

### property

The `property` filter returns an **array with only the specified property from the original objects**, not altering the `null` or `undefined` values.

Use it as follows:

```html
	<p>{{ myObjects | property:'myText' }}</p>
```

```javascript
	$scope.allTheTexts = $filter('property')($scope.myObjects, 'myText');
```

### join

The `join` filter returns **the original array as a string, with its elements joined with the specified separator**, if any, otherwise defaulting to the comma `,`.

Use it as follows:

```html
	<p>{{ myValues | join:', ' }}</p>
```

```javascript
	$scope.joinedValues = $filter('join')($scope.myValues, ', ');
```

## Development

### Test and build

To test and build the distribution files yourself, do the following:

```shell
npm install -g grunt-cli karma bower
npm install
bower install
grunt
```

These are the available grunt task:

* `karma:travis`, run karma tests once, on PhantomJS
* `karma:local`, run karma tests once, on Chrome
* `karma:dev`, run karma tests indefinitely after every file change, on Chrome
* `jshint:src`, run jshint on every source file
* `jshint:test`, run jshint on every test file
* `clean:dist`, clean the distribution directory
* `clean:temp`, clean the temporary directory
* `ngmin`, prepares every angular file into the `dist/.temp` directory
* `concat`, concatenates the module declaration and the `ngmin`-ified file from the `dist/.temp` into the `dist` directory, adding the banner
* `uglify`, minifies the output file in the `dist` directory, adding the banner
* `build`, builds the regular and minified file
* `test-travis`, runs `jshint` and `karma:travis`

Use the default task by calling `grunt` to run tests on PhantomJS and builds the regular and minified file.

### Contribute

To contribute, please follow the generic [AngularJS Contributing Guidelines](https://github.com/angular/angular.js/blob/master/CONTRIBUTING.md), with the only exception to send the PR to the `develop` branch instead of `master`.

## License

```
  Copyright 2014-2015 Francesco Pontillo

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
```