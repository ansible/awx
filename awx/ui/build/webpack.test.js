const path = require('path');

const _ = require('lodash');
const webpack = require('webpack');

const STATIC_URL = '/static/';

const development = require('./webpack.development');

const test = {
    plugins: [
        new webpack.DefinePlugin({
            $basePath: STATIC_URL
        })
    ]
};

test.plugins = development.plugins.concat(test.plugins);

module.exports = _.merge(development, test);

