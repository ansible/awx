
import axios from 'axios';
import React, { Component } from 'react';

import { withRouter } from 'react-router-dom';

import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';

import { withRootDialog } from './RootDialog';

import APIClient from '../api';

const NetworkContext = React.createContext({});

class Provider extends Component {
  constructor (props) {
    super(props);

    this.state = {
      value: {
        api: new APIClient(axios.create({ xsrfCookieName: 'csrftoken', xsrfHeaderName: 'X-CSRFToken' })),
        handleHttpError: err => {
          if (err.response.status === 401) {
            this.handle401();
          } else if (err.response.status === 404) {
            this.handle404();
          }
          return (err.response.status === 401 || err.response.status === 404);
        },
        ...props.value
      }
    };
  }

  handle401 () {
    const { handle401, history, setRootDialogMessage, i18n } = this.props;
    if (handle401) {
      handle401();
      return;
    }
    history.replace('/login');
    setRootDialogMessage({
      bodyText: i18n._(t`You have been logged out.`)
    });
  }

  handle404 () {
    const { handle404, history, setRootDialogMessage, i18n } = this.props;
    if (handle404) {
      handle404();
      return;
    }
    history.replace('/home');
    setRootDialogMessage({
      title: i18n._(t`404`),
      bodyText: i18n._(t`Cannot find resource.`),
      variant: 'warning'
    });
  }

  render () {
    const { value } = this.state;

    const { children } = this.props;

    return (
      <NetworkContext.Provider value={value}>
        {children}
      </NetworkContext.Provider>
    );
  }
}

export { Provider as _NetworkProvider };
export const NetworkProvider = withI18n()(withRootDialog(withRouter(Provider)));

export function withNetwork (Child) {
  return (props) => (
    <NetworkContext.Consumer>
      {context => <Child {...props} {...context} />}
    </NetworkContext.Consumer>
  );
}
