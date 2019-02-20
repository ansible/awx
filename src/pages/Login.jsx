import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  LoginForm,
  LoginPage,
} from '@patternfly/react-core';

import towerLogo from '../../images/tower-logo-header.svg';

class AWXLogin extends Component {
  constructor (props) {
    super(props);

    this.state = {
      username: '',
      password: '',
      isInputValid: true,
      isLoading: false
    };

    this.onChangeUsername = this.onChangeUsername.bind(this);
    this.onChangePassword = this.onChangePassword.bind(this);
    this.onLoginButtonClick = this.onLoginButtonClick.bind(this);
  }

  onChangeUsername (value) {
    this.setState({ username: value, isInputValid: true });
  }

  onChangePassword (value) {
    this.setState({ password: value, isInputValid: true });
  }

  async onLoginButtonClick (event) {
    const { username, password, isLoading } = this.state;
    const { api } = this.props;

    event.preventDefault();

    if (isLoading) {
      return;
    }

    this.setState({ isLoading: true });

    try {
      await api.login(username, password);
    } catch (error) {
      if (error.response && error.response.status === 401) {
        this.setState({ isInputValid: false });
      }
    } finally {
      this.setState({ isLoading: false });
    }
  }

  render () {
    const { username, password, isInputValid } = this.state;
    const { api, alt, loginInfo, logo } = this.props;
    const logoSrc = logo ? `data:image/jpeg;${logo}` : towerLogo;

    if (api.isAuthenticated()) {
      return (<Redirect to="/" />);
    }

    return (
      <I18n>
        {({ i18n }) => (
          <LoginPage
            brandImgSrc={logoSrc}
            brandImgAlt={alt || 'Ansible Tower'}
            loginTitle={i18n._(t`Welcome to Ansible Tower! Please Sign In.`)}
            textContent={loginInfo}
          >
            <LoginForm
              usernameLabel={i18n._(t`Username`)}
              passwordLabel={i18n._(t`Password`)}
              showHelperText={!isInputValid}
              helperText={i18n._(t`Invalid username or password. Please try again.`)}
              usernameValue={username}
              passwordValue={password}
              isValidUsername={isInputValid}
              isValidPassword={isInputValid}
              onChangeUsername={this.onChangeUsername}
              onChangePassword={this.onChangePassword}
              onLoginButtonClick={this.onLoginButtonClick}
            />
          </LoginPage>
        )}
      </I18n>
    );
  }
}

export default AWXLogin;
