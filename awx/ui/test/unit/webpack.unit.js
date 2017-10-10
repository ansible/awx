const webpack = require('webpack');
const merge = require('webpack-merge');
const base = require('../../build/webpack.base');

const STATIC_URL = '/static/';

const test = {
    devtool: 'cheap-source-map',
    plugins: [
        new webpack.DefinePlugin({
            $basePath: STATIC_URL
        })
    ]
};

module.exports = merge(base, test);
