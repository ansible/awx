const path = require('path');
const webpack = require('webpack');

const TARGET_PORT = process.env.TARGET_PORT || 8043;
const TARGET_HOST = process.env.TARGET_HOST || 'localhost';
const TARGET = `https://${TARGET_HOST}:${TARGET_PORT}`;

const ROOT_PATH = __dirname;
const SRC_PATH = path.join(ROOT_PATH, 'src');

module.exports = {
  entry: './src/index.jsx',
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        loader: 'babel-loader'
      },
      {
        test: /\.s?[ac]ss$/,
        use: [
          { loader: 'style-loader' },
          { loader: 'css-loader' },
          { loader: 'sass-loader' },
        ]
      },
      {
        test: /\.(woff(2)?|ttf|eot)(\?v=\d+\.\d+\.\d+)?$/,
        use: [{
          loader: 'file-loader',
          options: {
            name: '[name].[ext]',
            outputPath: 'assets/fonts/',
            publicPath: 'assets/fonts',
            includePaths: [
              'node_modules/@patternfly/patternfly/assets/fonts',
            ]
          }
        }]
      },
      {
        test: /\.(jpg|png|gif|svg)(\?v=\d+\.\d+\.\d+)?$/,
        use: [{
          loader: 'file-loader',
          options: {
            name: '[name].[ext]',
            outputPath: 'assets/images/',
            publicPath: 'assets/images',
            includePaths: [
              'node_modules/@patternfly/patternfly/assets/images',
            ]
          }
        }]
      }
    ]
  },
  resolve: {
    extensions: ['*', '.js', '.jsx', '.css'],
    alias: {
      '@api': path.join(SRC_PATH, 'api'),
      '@components': path.join(SRC_PATH, 'components'),
      '@contexts': path.join(SRC_PATH, 'contexts'),
      '@screens': path.join(SRC_PATH, 'screens'),
      '@types': path.join(SRC_PATH, 'types'),
      '@util': path.join(SRC_PATH, 'util'),
      '@testUtils': path.join(ROOT_PATH, 'testUtils'),
    }
  },
  output: {
    path: path.resolve(__dirname, '/dist'),
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
    host: '0.0.0.0',
    disableHostCheck: true,
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
      }
    ]
  },
  // https://github.com/lingui/js-lingui/issues/408
  node: {
    fs: 'empty'
  }
};
