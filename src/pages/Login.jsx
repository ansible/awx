import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';
import {
  LoginForm,
  LoginPage,
} from '@patternfly/react-core';

import towerLogo from '../../images/tower-logo-header.svg';
import api from '../api';

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
    const logoAlt = alt || 'Ansible Tower';
    const LOGIN_ERROR_MESSAGE = 'Invalid username or password. Please try again.';
    const LOGIN_TITLE = 'Welcome to Ansible Tower! Please Sign In.';
    const LOGIN_USERNAME = 'Username';
    const LOGIN_PASSWORD = 'Password';

    if (api.isAuthenticated()) {
      return (<Redirect to="/" />);
    }

    return (
      <LoginPage
        mainBrandImgSrc={logoSrc}
        mainBrandImgAlt={logoAlt}
        loginTitle={LOGIN_TITLE}
      >
        <LoginForm
          usernameLabel={LOGIN_USERNAME}
          usernameValue={username}
          onChangeUsername={this.handleUsernameChange}
          passwordLabel={LOGIN_PASSWORD}
          passwordValue={password}
          onChangePassword={this.handlePasswordChange}
          isValidPassword={isValidPassword}
          passwordHelperTextInvalid={LOGIN_ERROR_MESSAGE}
          onLoginButtonClick={this.handleSubmit}
        />
      </LoginPage>
    );
  }
}

export default AtLogin;
