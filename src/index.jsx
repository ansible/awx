import React from 'react';
import { render } from 'react-dom';

import App from './App';
import api from './api';
import { API_ROOT } from './endpoints';

import '@patternfly/react-core/dist/styles/base.css';
import '@patternfly/patternfly-next/patternfly.css';

import './app.scss';
import './components/Pagination/styles.scss';
import './components/DataListToolbar/styles.scss';

const el = document.getElementById('app');

const main = async () => {
    const { custom_logo, custom_login_info } = await api.get(API_ROOT);
    render(<App logo={custom_logo} loginInfo={custom_login_info} />, el);
};

main();

export default main;
