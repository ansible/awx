import React from 'react';
import { render } from 'react-dom';

import App from './App';
import api from './api';

import '@patternfly/react-core/dist/styles/base.css';
import '@patternfly/patternfly-next/patternfly.css';

import './app.scss';

const el = document.getElementById('app');

api.getRoot()
  .then(({ data }) => {
    const { custom_logo, custom_login_info } = data;

    render(<App logo={custom_logo} loginInfo={custom_login_info} />, el);
  });
