module.exports = api => {
  api.cache(false);
  return {
    plugins: [
      'babel-plugin-styled-components',
      '@babel/plugin-proposal-class-properties',
      'macros'
    ],
    presets: [
      ['@babel/preset-env', {
        targets: {
          node: '8.11'
        }
      }],
      '@babel/preset-react'
    ]
  };
};
