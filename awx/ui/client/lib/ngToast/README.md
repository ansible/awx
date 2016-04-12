ngToast [![Code Climate](http://img.shields.io/codeclimate/github/tameraydin/ngToast.svg?style=flat-square)](https://codeclimate.com/github/tameraydin/ngToast/dist/ngToast.js) [![Build Status](http://img.shields.io/travis/tameraydin/ngToast/master.svg?style=flat-square)](https://travis-ci.org/tameraydin/ngToast)
=======

ngToast is a simple Angular provider for toast notifications.

**[Demo](http://tameraydin.github.io/ngToast)**

## Usage

1. Install via [Bower](http://bower.io/) or [NPM](http://www.npmjs.org):
  ```bash
  bower install ngtoast --production
  # or
  npm install ng-toast --production
  ```
  or manually [download](https://github.com/tameraydin/ngToast/archive/master.zip).

2. Include ngToast source files and dependencies ([ngSanitize](http://docs.angularjs.org/api/ngSanitize), [Bootstrap CSS](http://getbootstrap.com/)):
  ```html
  <link rel="stylesheet" href="bower/bootstrap/dist/css/bootstrap.min.css">
  <link rel="stylesheet" href="bower/ngtoast/dist/ngToast.min.css">
  
  <script src="bower/angular-sanitize/angular-sanitize.min.js"></script>
  <script src="bower/ngtoast/dist/ngToast.min.js"></script>
  ```
 *Note: only the [Alerts](http://getbootstrap.com/components/#alerts) component is used as style base, so you don't have to include complete CSS*

3. Include ngToast as a dependency in your application module:
  ```javascript
  var app = angular.module('myApp', ['ngToast']);
  ```

4. Place `toast` element into your HTML:
  ```html
  <body>
    <toast></toast>
    ...
  </body>
  ```

5. Inject ngToast provider in your controller:
  ```javascript
  app.controller('myCtrl', function(ngToast) {
    ngToast.create('a toast message...');
  });
  // for more info: http://tameraydin.github.io/ngToast/#api
  ```

## Animations
ngToast comes with optional animations. In order to enable animations in ngToast, you need to include [ngAnimate](http://docs.angularjs.org/api/ngAnimate) module into your app:

```html
<script src="bower/angular-animate/angular-animate.min.js"></script>
```

**Built-in**
  1. Include the ngToast animation stylesheet:
  
  ```html
  <link rel="stylesheet" href="bower/ngtoast/dist/ngToast-animations.min.css">
  ```

  2. Set the `animation` option.
  ```javascript
  app.config(['ngToastProvider', function(ngToastProvider) {
    ngToastProvider.configure({
      animation: 'slide' // or 'fade'
    });
  }]);
  ```
  Built-in ngToast animations include `slide` & `fade`.
  
**Custom**
  
  See the [plunker](http://plnkr.co/edit/wglAvsCuTLLykLNqVGwU) using [animate.css](http://daneden.github.io/animate.css/).
  
  1. Using the `additionalClasses` option and [ngAnimate](http://docs.angularjs.org/api/ngAnimate) you can easily add your own animations or wire up 3rd party css animations.
  ```javascript
  app.config(['ngToastProvider', function(ngToastProvider) {
    ngToastProvider.configure({
      additionalClasses: 'my-animation'
    });
  }]);
  ```

  2. Then in your CSS (example using animate.css):
  ```css
  /* Add any vendor prefixes you need */
  .my-animation.ng-enter {
    animation: flipInY 1s;
  }
  
  .my-animation.ng-leave {
    animation: flipOutY 1s;
  }
  ```

## Settings & API

Please find at the [project website](http://tameraydin.github.io/ngToast/#api).

## Development

* Clone the repo or [download](https://github.com/tameraydin/ngToast/archive/master.zip)
* Install dependencies: ``npm install && bower install``
* Run ``grunt watch``, play on **/src**
* Build: ``grunt``

## License

MIT [http://tameraydin.mit-license.org/](http://tameraydin.mit-license.org/)

## Maintainers

- [Tamer Aydin](http://tamerayd.in)
- [Levi Thomason](http://www.levithomason.com)

## TODO
- Add more unit & e2e tests
