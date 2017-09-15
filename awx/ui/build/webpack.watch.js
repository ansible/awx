const path = require('path');

const _ = require('lodash');
const webpack = require('webpack');
const HtmlWebpackHarddiskPlugin = require('html-webpack-harddisk-plugin');

const TARGET_PORT = _.get(process.env, 'npm_package_config_django_port', 8043);
const TARGET_HOST = _.get(process.env, 'npm_package_config_django_host', 'https://localhost');
const TARGET = `https://${TARGET_HOST}:${TARGET_PORT}`;

let development = require('./webpack.development');

let watch = {
    plugins: [
        new HtmlWebpackHarddiskPlugin(),
        new webpack.HotModuleReplacementPlugin()
    ],
    devServer: {
        contentBase: path.resolve(__dirname, '..', 'static'),
        stats: 'minimal',
        publicPath: '/static/',
        host: '127.0.0.1',
        port: 3000,
        proxy: {
            '/': {
                target: TARGET,
                secure: false,
                ws: false
            },
            '/websocket': {
                target: TARGET,
                secure: false,
                ws: true
            }
        }
    }
};

watch.plugins = development.plugins.concat(watch.plugins)

module.exports = _.merge(development, watch);

