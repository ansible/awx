const path = require('path');

const webpack = require('webpack');
const merge = require('webpack-merge');
const base = require(path.resolve(__dirname, '../..', 'build/webpack.base'));

const STATIC_URL = '/static/';

const test = {
    devtool: 'inline-source-map',
    plugins: [
        new webpack.DefinePlugin({
            $basePath: STATIC_URL
        })
    ]
};

module.exports = merge(base, test);
