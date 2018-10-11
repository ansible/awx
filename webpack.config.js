const webpack = require('webpack');
const TARGET_PORT = 8043;
const TARGET = `https://localhost:${TARGET_PORT}`;

module.exports = {
  entry: './src/index.js',
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: ['babel-loader']
      },
      {
        test: /\.s?[ac]ss$/,
        use: [
          { loader: 'style-loader' },
          { loader: 'css-loader' },
          {
            loader: 'sass-loader',
            options: {
              includePaths: [
                'node_modules/patternfly/dist/sass',
                'node_modules/patternfly/node_modules/bootstrap-sass/assets/stylesheet',
                'node_modules/patternfly/node_modules/font-awesome-sass/assets/stylesheets'
              ]
            }
          }
        ]
      },
      {
        test: /\.(woff(2)?|ttf|jpg|png|eot|gif|svg)(\?v=\d+\.\d+\.\d+)?$/,
        use: [{
            loader: 'file-loader',
            options: {
                name: '[name].[ext]',
                outputPath: 'fonts/',
                publicPatH: '../'
            }
        }]
      }
    ]
  },
  resolve: {
    extensions: ['*', '.js', '.jsx', '.css']
  },
  output: {
    path: __dirname + '/dist',
    publicPath: '/',
    filename: 'bundle.js'
  },
  plugins: [
    new webpack.HotModuleReplacementPlugin()
  ],
  devServer: {
    contentBase: './dist',
    hot: true,
    inline: true,
    stats: 'minimal',
    host: '127.0.0.1',
    https: true,
    port: 3001,
    clientLogLevel: 'none',
    proxy: [
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
        context: '/api',
        target: TARGET,
        secure: false,
        ws: false,
        bypass: req => (req.originalUrl.includes('hot-update.json') || req.originalUrl.includes('login')),
    },
    {
        context: '/websocket',
        target: TARGET,
        secure: false,
        ws: true
    }]
  }
};
