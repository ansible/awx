import React from 'react';
import ReactDOM from 'react-dom';
import '@patternfly/react-core/dist/styles/base.css';
import App from './App';
import { BrandName } from './variables';

document.title = `Ansible ${BrandName}`;

ReactDOM.render(
  <App />,
  document.getElementById('app') || document.createElement('div')
);
