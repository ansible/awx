const path = require('path');

const _ = require('lodash');

const base = require('./webpack.base');

const development = {
    devtool: 'cheap-source-map'
};

module.exports = _.merge(base, development);
