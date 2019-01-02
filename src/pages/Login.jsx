import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';
import { I18n } from '@lingui/react';
import { t } from '@lingui/macro';
import {
  LoginForm,
  LoginPage,
} from '@patternfly/react-core';

import towerLogo from '../../images/tower-logo-header.svg';
import api from '../api';

import Background from '../components/Background';

class AtLogin extends Component {
  constructor (props) {
    super(props);

    this.state = {
      username: '',
      password: '',
      isValidPassword: true,
      loading: false
    };
  }

  componentWillUnmount () {
    this.unmounting = true; // todo: state management
  }

  safeSetState = obj => !this.unmounting && this.setState(obj);

  handleUsernameChange = value => this.safeSetState({ username: value, isValidPassword: true });

  handlePasswordChange = value => this.safeSetState({ password: value, isValidPassword: true });

  handleSubmit = async event => {
    const { username, password, loading } = this.state;

    event.preventDefault();

    if (!loading) {
      this.safeSetState({ loading: true });

      try {
        await api.login(username, password);
      } catch (error) {
        if (error.response.status === 401) {
          this.safeSetState({ isValidPassword: false });
        }
      } finally {
        this.safeSetState({ loading: false });
      }
    }
  }

  render () {
    const { username, password, isValidPassword } = this.state;
    const { logo, alt } = this.props;
    const logoSrc = logo ? `data:image/jpeg;${logo}` : towerLogo;

    if (api.isAuthenticated()) {
      return (<Redirect to="/" />);
    }

    return (
      <I18n>
        {({ i18n }) => (
          <Background>
            <LoginPage
              brandImgSrc={logoSrc}
              brandImgAlt={alt || 'Ansible Tower'}
              loginTitle={i18n._(t`Welcome to Ansible Tower! Please Sign In.`)}
            >
              <LoginForm
                usernameLabel={i18n._(t`Username`)}
                usernameValue={username}
                onChangeUsername={this.handleUsernameChange}
                passwordLabel={i18n._(t`Password`)}
                passwordValue={password}
                onChangePassword={this.handlePasswordChange}
                isValidPassword={isValidPassword}
                passwordHelperTextInvalid={i18n._(t`Invalid username or password. Please try again.`)}
                onLoginButtonClick={this.handleSubmit}
              />
            </LoginPage>
          </Background>
        )}
      </I18n>
    );
  }
}

export default AtLogin;
