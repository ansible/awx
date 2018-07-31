const path = require('path');

const _ = require('lodash');
const webpack = require('webpack');
const merge = require('webpack-merge');
const nodeObjectHash = require('node-object-hash');
const HardSourceWebpackPlugin = require('hard-source-webpack-plugin');
const HtmlWebpackHarddiskPlugin = require('html-webpack-harddisk-plugin');

const TARGET_PORT = _.get(process.env, 'npm_package_config_django_port', 8043);
const TARGET_HOST = _.get(process.env, 'npm_package_config_django_host', 'https://localhost');
const TARGET = `https://${TARGET_HOST}:${TARGET_PORT}`;
const OUTPUT = 'js/[name].js';

const development = require('./webpack.development');

const watch = {
    cache: true,
    devtool: 'cheap-source-map',
    output: {
        filename: OUTPUT
    },
     module: {
         rules: [
             {
                 test: /\.js$/,
                 enforce: 'pre',
                 exclude: /node_modules/,
                 loader: 'eslint-loader'
             }
         ]
     },
    plugins: [
        new HtmlWebpackHarddiskPlugin(),
        new HardSourceWebpackPlugin({
            cacheDirectory: 'node_modules/.cache/hard-source/[confighash]',
            recordsPath: 'node_modules/.cache/hard-source/[confighash]/records.json',
            configHash: config => nodeObjectHash({ sort: false }).hash(config),
            environmentHash: {
                root: process.cwd(),
                directories: ['node_modules'],
                files: ['package.json']
            }
        }),
        new webpack.HotModuleReplacementPlugin()
    ],
    devServer: {
        hot: true,
        inline: true,
        contentBase: path.resolve(__dirname, '..', 'static'),
        stats: 'minimal',
        publicPath: '/static/',
        host: '127.0.0.1',
        https: true,
        port: 3000,
        clientLogLevel: 'none',
        proxy: [{
            context: (pathname, req) => !(pathname === '/api/login/' && req.method === 'POST'),
            target: TARGET,
            secure: false,
            ws: false,
            bypass: req => req.originalUrl.includes('hot-update.json')
        },
        {
            context: '/api/login/',
            target: TARGET,
            secure: false,
            ws: false,
            headers: {
                Host: `localhost:${TARGET_PORT}`,
                Origin: TARGET,
                Referer: `${TARGET}/`
            }
        },
        {
            context: '/websocket',
            target: TARGET,
            secure: false,
            ws: true
        }]
    }
};

module.exports = merge(development, watch);
