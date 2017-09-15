const path = require('path');

const webpack = require('webpack');
const CleanWebpackPlugin = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const HtmlWebpackPlugin = require('html-webpack-plugin');

const CLIENT_PATH = path.resolve(__dirname, '../client');
const LIB_PATH = path.join(CLIENT_PATH, 'lib');
const UI_PATH = path.resolve(__dirname, '..');

const ASSETS_PATH = path.join(CLIENT_PATH, 'assets');
const COMPONENTS_PATH = path.join(LIB_PATH, 'components');
const COVERAGE_PATH = path.join(UI_PATH, 'coverage');
const FEATURES_PATH = path.join(CLIENT_PATH, 'features');
const LANGUAGES_PATH = path.join(CLIENT_PATH, 'languages');
const MODELS_PATH = path.join(LIB_PATH, 'models');
const NODE_MODULES_PATH = path.join(UI_PATH, 'node_modules');
const SERVICES_PATH = path.join(LIB_PATH, 'services');
const SOURCE_PATH = path.join(CLIENT_PATH, 'src');
const STATIC_PATH = path.join(UI_PATH, 'static');

const APP_ENTRY = path.join(SOURCE_PATH, 'app.js');
const VENDOR_ENTRY = path.join(SOURCE_PATH, 'vendor.js');
const INDEX_ENTRY = path.join(CLIENT_PATH, 'index.template.ejs');
const INDEX_OUTPUT = path.join(UI_PATH, 'templates/ui/index.html');
const THEME_ENTRY = path.join(LIB_PATH, 'theme', 'index.less');
const OUTPUT = 'js/[name].[hash].js';
const CHUNKS = ['vendor', 'app'];

const VENDOR = VENDOR_ENTRY;
const APP = [THEME_ENTRY, APP_ENTRY];

let base = {
    entry: {
        vendor: VENDOR,
        app: APP
    },
    output: {
        path: STATIC_PATH,
        publicPath: '',
        filename: OUTPUT
    },
    stats: 'minimal',
    module: {
        rules: [
            {
                test: /\.js$/,
                loader: 'babel-loader',
                exclude: /node_modules/,
                options: {
                    presets: ['env']
                }
            },
            {
                test: /\.css$/,
                use: ExtractTextPlugin.extract({
                    use: {
                        loader: 'css-loader',
                        options: {
                            url: false
                        }
                    }
                })
            },
            {
                test: /\lib\/theme\/index.less$/,
                use: ExtractTextPlugin.extract({
                    use: ['css-loader', 'less-loader']
                })
            },
            {
                test: require.resolve('jquery'),
                loader: 'expose-loader?$!expose-loader?jQuery!expose-loader?jquery'
            },
            {
                loader: 'script-loader',
                test: [
                    /node_modules\/javascript-detect-element-resize\/jquery.resize\.js$/,
                    /node_modules\/d3\/d3\.min.js$/
                ]
            },
            {
                test: /\.js$/,
                use: 'imports-loader?define=>false'
            },
            {
                test: /\.html$/,
                use: ['ngtemplate-loader', 'html-loader'],
                include: [
                    /lib\/components\//,
                    /features\//
                ]
            },
            {
                test: /\.json$/,
                loader: 'json-loader',
                exclude: /node_modules/
            }
        ]
    },
    plugins: [
        new webpack.ProvidePlugin({
            jsyaml: 'js-yaml',
            CodeMirror: 'codemirror',
            jsonlint: 'codemirror.jsonlint',
            _: 'lodash'
        }),
        new ExtractTextPlugin('css/[name].[hash].css'),
        new CleanWebpackPlugin([STATIC_PATH, COVERAGE_PATH, LANGUAGES_PATH], {
            root: UI_PATH,
            verbose: false
        }),
        new CopyWebpackPlugin([
            {
                from: path.join(ASSETS_PATH, 'fontcustom/**/*'),
                to: path.join(STATIC_PATH, 'fonts/'),
                flatten: true
            },
            {
                from: path.join(NODE_MODULES_PATH, 'components-font-awesome/fonts/*'),
                to: path.join(STATIC_PATH, 'fonts/'),
                flatten: true
            },
            {
                from: path.join(ASSETS_PATH, 'custom-theme/images.new/*'),
                to: path.join(STATIC_PATH, 'images/'),
                flatten: true
            },
            {
                from: path.join(LANGUAGES_PATH, '*'),
                to: path.join(STATIC_PATH, 'languages'),
                flatten: true
            },
            {
                from: ASSETS_PATH,
                to: path.join(STATIC_PATH, 'assets')
            },
            {
                from: path.join(NODE_MODULES_PATH, 'angular-scheduler/lib/*.html'),
                to: path.join(STATIC_PATH, 'lib'),
                context: NODE_MODULES_PATH
            },
            {
                from: path.join(NODE_MODULES_PATH, 'angular-tz-extensions/tz/data/*'),
                to: path.join(STATIC_PATH, 'lib/'),
                context: NODE_MODULES_PATH
            },
            {
                from: path.join(SOURCE_PATH, '**/*.partial.html'),
                to: path.join(STATIC_PATH, 'partials/'),
                context: SOURCE_PATH
            },
            {
                from: path.join(SOURCE_PATH, 'partials', '*.html'),
                to: STATIC_PATH,
                context: SOURCE_PATH
            },
            {
                from: path.join(SOURCE_PATH, '*config.js'),
                to: STATIC_PATH,
                flatten: true
            }
        ]),
        new HtmlWebpackPlugin({
            alwaysWriteToDisk: true,
            template: INDEX_ENTRY,
            filename: INDEX_OUTPUT,
            inject: false,
            chunks: CHUNKS,
            chunksSortMode: (moduleA, moduleB) => {
                moduleA.files.sort((fileA, fileB) => fileA.includes('js') ? -1 : 1)
                moduleB.files.sort((fileA, fileB) => fileA.includes('js') ? -1 : 1)

                return moduleA.names[0] === 'vendor' ? -1 : 1
            }
        })
    ],
    resolve: {
        alias: {
            '~features': FEATURES_PATH,
            '~models': MODELS_PATH,
            '~services': SERVICES_PATH,
            '~components': COMPONENTS_PATH,
            '~modules': NODE_MODULES_PATH,
            '~assets': ASSETS_PATH,
            'd3$': '~modules/d3/d3.min.js',
            'codemirror.jsonlint$': '~modules/codemirror/addon/lint/json-lint.js',
            'jquery-resize$': '~modules/javascript-detect-element-resize/jquery.resize.js',
            'select2$': '~modules/select2/dist/js/select2.full.min.js',
            'js-yaml$': '~modules/js-yaml/dist/js-yaml.min.js',
            'lr-infinite-scroll$': '~modules/lr-infinite-scroll/lrInfiniteScroll.js',
            'angular-ui-router$': '~modules/angular-ui-router/release/angular-ui-router.js',
            'angular-ui-router-state-events$': '~modules/angular-ui-router/release/stateEvents.js',
            'ng-toast-provider$': '~modules/ng-toast/src/scripts/provider.js',
            'ng-toast-directives$': '~modules/ng-toast/src/scripts/directives.js',
            'ng-toast$': '~modules/ng-toast/src/scripts/module.js'
        }
    }
};

module.exports = base;
