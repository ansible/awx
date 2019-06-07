import React, { Component } from 'react';

import { withNetwork } from './Network';

import { ConfigAPI, MeAPI, RootAPI } from '../api';

const ConfigContext = React.createContext({});

class Provider extends Component {
  constructor (props) {
    super(props);

    this.state = {
      value: {
        ansible_version: null,
        custom_virtualenvs: null,
        version: null,
        custom_logo: null,
        custom_login_info: null,
        me: {},
        ...props.value
      }
    };

    this.fetchConfig = this.fetchConfig.bind(this);
    this.fetchMe = this.fetchMe.bind(this);
    this.updateConfig = this.updateConfig.bind(this);
  }

  componentDidMount () {
    const { value } = this.props;
    if (!value) {
      this.fetchConfig();
    }
  }

  updateConfig = config => {
    const { ansible_version, custom_virtualenvs, version } = config;

    this.setState(prevState => ({
      value: {
        ...prevState.value,
        ansible_version,
        custom_virtualenvs,
        version
      }
    }));
  };

  async fetchMe () {
    const { handleHttpError } = this.props;
    try {
      const {
        data: {
          results: [me]
        }
      } = await MeAPI.read();
      this.setState(prevState => ({
        value: {
          ...prevState.value,
          me
        }
      }));
    } catch (err) {
      handleHttpError(err)
        || this.setState({
          value: {
            ansible_version: null,
            custom_virtualenvs: null,
            version: null,
            custom_logo: null,
            custom_login_info: null,
            me: {}
          }
        });
    }
  }

  async fetchConfig () {
    const { handleHttpError } = this.props;

    try {
      const [configRes, rootRes, meRes] = await Promise.all([
        ConfigAPI.read(),
        RootAPI.read(),
        MeAPI.read()
      ]);
      this.setState({
        value: {
          ansible_version: configRes.data.ansible_version,
          custom_virtualenvs: configRes.data.custom_virtualenvs,
          version: configRes.data.version,
          custom_logo: rootRes.data.custom_logo,
          custom_login_info: rootRes.data.custom_login_info,
          me: meRes.data.results[0]
        }
      });
    } catch (err) {
      handleHttpError(err)
        || this.setState({
          value: {
            ansible_version: null,
            custom_virtualenvs: null,
            version: null,
            custom_logo: null,
            custom_login_info: null,
            me: {}
          }
        });
    }
  }

  render () {
    const { value } = this.state;

    const { children } = this.props;

    return (
      <ConfigContext.Provider
        value={{
          ...value,
          fetchMe: this.fetchMe,
          updateConfig: this.updateConfig
        }}
      >
        {children}
      </ConfigContext.Provider>
    );
  }
}

export const ConfigProvider = withNetwork(Provider);

export const Config = ({ children }) => (
  <ConfigContext.Consumer>{value => children(value)}</ConfigContext.Consumer>
);
