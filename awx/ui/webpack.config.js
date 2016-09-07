var path = require('path'),
    webpack = require('webpack');

var vendorPkgs = [
    'angular',
    'angular-breadcrumb',
    'angular-codemirror',
    'angular-cookies',
    'angular-drag-and-drop-lists',
    'angular-md5',
    'angular-moment',
    'angular-sanitize',
    'angular-scheduler',
    'angular-tz-extensions',
    'angular-ui-router',
    'bootstrap',
    'bootstrap-datepicker',
    'codemirror',
    'd3',
    //'javascript-detect-element-resize', // jquery-flavored dist is alias'd below
    'jquery',
    'jquery-ui',
    'js-yaml',
    'lodash',
    'lr-infinite-scroll',
    'moment',
    'ng-toast',
    'nvd3',
    'select2',
    'socket.io-client',
];

var dev = {
    entry: {
        app: './client/src/app.js',
        vendor: vendorPkgs
    },
    output: {
        path: './static/',
        filename: 'tower.js'
    },
    plugins: [
        // vendor shims:
        // [{expected_local_var : dependency}, ...]
        new webpack.ProvidePlugin({
            '$': 'jquery',
            'jQuery': 'jquery',
            'window.jQuery': 'jquery',
            '_': 'lodash',
            'CodeMirror': 'codemirror',
            'jsyaml': 'js-yaml',
            'jsonlint': 'codemirror.jsonlint',
            'RRule': 'rrule'
        }),
        // (chunkName, outfileName)
        new webpack.optimize.CommonsChunkPlugin('vendor', 'tower.vendor.js'),
    ],
    module: {
        preLoaders: [{
            test: /\.js?$/,
            loader: 'jshint-loader',
            exclude: ['/(node_modules)/'],
            include: [path.resolve() + '/client/src/'],
            jshint: {
                emitErrors: true
            }
        }],
        loaders: [
        {   // expose RRule global for nlp module, whose AMD/CJS loading methods are broken
            test: /\.rrule.js$/,
            loader: 'expose?RRule'
        },
        {
            test: /\.nlp.js$/,
            // disable CommonJS & AMD loading (broken in this lib)
            loader: 'imports?require=>false&define=>false'
        },
        {
            // disable AMD loading (broken in this lib) and default to CommonJS (not broken)
            test: /\.angular-tz-extensions.js$/,
            loader: 'imports?define=>false'
        }, {
            // es6 -> es5
            test: /\.js$/,
            loader: 'babel-loader',
            exclude: /(node_modules)/,
            query: {
                presets: ['es2015']
            }
        }, {
            test: /\.nlp.js$/,
            loader: 'imports?RRule=rrule'
        }]
    },
    resolve: {
        alias: {
            'codemirror.jsonlint': path.resolve() + '/node_modules/codemirror/addon/lint/json-lint.js',
            'jquery.resize': path.resolve() + '/node_modules/javascript-detect-element-resize/jquery.resize.js',
            'select2': path.resolve() + '/node_modules/select2/dist/js/select2.full.js'
        }
    },
    devtool: 'sourcemap',
    watch: true,
};

var release = {
    entry: {
        app: './client/src/app.js',
        vendor: vendorPkgs
    },
    output: {
        path: './static/',
        filename: 'tower.js'
    },
    plugins: [
        // vendor shims:
        // [{expected_local_var : dependency}, ...]
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            'window.jQuery': 'jquery',
            _: 'lodash',
            'CodeMirror': 'codemirror',
            'jsyaml': 'js-yaml',
            'jsonlint': 'codemirror.jsonlint'
        }),
        new webpack.optimize.CommonsChunkPlugin('vendor', 'tower.vendor.js'),
        new webpack.optimize.UglifyJsPlugin({
            mangle: false
        })
    ],
    module: {
        loaders: [{
            test: /\.rrule.js$/,
            loader: 'expose?RRule'
        },
        {
            test: /\.nlp.js$/,
            // disable CommonJS (broken in this lib)
            loader: 'imports?require=>false'
        },
        {
            // disable AMD loading (broken in this lib) and default to CommonJS (not broken)
            test: /\.angular-tz-extensions.js$/,
            loader: 'imports?define=>false!'
        }, {
            // es6 -> es5
            test: /\.js$/,
            loader: 'babel-loader',
            exclude: /(node_modules)/,
            query: {
                presets: ['es2015']
            }
        }, ]
    },
    resolve: {
        alias: {
            'codemirror.jsonlint': path.resolve() + '/node_modules/codemirror/addon/lint/json-lint.js',
            'jquery.resize': path.resolve() + '/node_modules/javascript-detect-element-resize/jquery.resize.js',
            'select2': path.resolve() + '/node_modules/select2/dist/js/select2.full.js'
        }
    }
};

module.exports = { dev: dev, release: release };
