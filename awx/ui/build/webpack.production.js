const _ = require('lodash');

const webpack = require('webpack');
const UglifyJSPlugin = require('uglifyjs-webpack-plugin');

let base = require('./webpack.base');

let production = {
    plugins: [
        new UglifyJSPlugin({
            compress: true,
            mangle: false
        })
    ]
};

production.plugins = base.plugins.concat(production.plugins)

module.exports = _.merge(base, production);
