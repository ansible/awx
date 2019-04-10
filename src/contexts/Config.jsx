
import React, { Component } from 'react';

import { withNetwork } from './Network';

const ConfigContext = React.createContext({});

class provider extends Component {
  constructor (props) {
    super(props);

    this.state = {
      value: {
        ansible_version: null,
        custom_virtualenvs: null,
        version: null,
        custom_logo: null,
        custom_login_info: null
      }
    };

    this.fetchConfig = this.fetchConfig.bind(this);
  }

  componentDidMount () {
    this.fetchConfig();
  }

  async fetchConfig () {
    const { api, handleHttpError } = this.props;

    try {
      const {
        data: {
          ansible_version,
          custom_virtualenvs,
          version
        }
      } = await api.getConfig();
      const {
        data: {
          custom_logo,
          custom_login_info
        }
      } = await api.getRoot();
      this.setState({
        value: {
          ansible_version,
          custom_virtualenvs,
          version,
          custom_logo,
          custom_login_info
        }
      });
    } catch (err) {
      handleHttpError(err) || this.setState({
        value: {
          ansible_version: null,
          custom_virtualenvs: null,
          version: null,
          custom_logo: null,
          custom_login_info: null
        }
      });
    }
  }

  render () {
    const {
      value: stateValue
    } = this.state;

    const { value: propsValue, children } = this.props;

    return (
      <ConfigContext.Provider value={propsValue || stateValue}>
        {children}
      </ConfigContext.Provider>
    );
  }
}

export const ConfigProvider = withNetwork(provider);

export const Config = ({ children }) => (
  <ConfigContext.Consumer>
    {value => children(value)}
  </ConfigContext.Consumer>
);
