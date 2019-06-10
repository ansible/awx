import React, { Component } from 'react';
import { Redirect, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import {
  LoginForm,
  LoginPage as PFLoginPage,
} from '@patternfly/react-core';

import { withRootDialog } from '../contexts/RootDialog';
import { withNetwork } from '../contexts/Network';
import { RootAPI } from '../api';
import { BrandName } from '../variables';

import logoImg from '../../images/brand-logo.svg';

const LoginPage = styled(PFLoginPage)`
  & .pf-c-brand {
    max-height: 285px;
  }
`;

class AWXLogin extends Component {
  constructor (props) {
    super(props);

    this.state = {
      username: '',
      password: '',
      isInputValid: true,
      isLoading: false,
      isAuthenticated: false
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
    const { handleHttpError, clearRootDialogMessage, fetchMe, updateConfig } = this.props;

    event.preventDefault();

    if (isLoading) {
      return;
    }

    clearRootDialogMessage();
    this.setState({ isLoading: true });

    try {
      const { data } = await RootAPI.login(username, password);
      updateConfig(data);
      await fetchMe();
      this.setState({ isAuthenticated: true, isLoading: false });
    } catch (error) {
      handleHttpError(error) || this.setState({ isInputValid: false, isLoading: false });
    }
  }

  render () {
    const { username, password, isInputValid, isAuthenticated } = this.state;
    const { alt, loginInfo, logo, bodyText: errorMessage, i18n } = this.props;
    const logoSrc = logo ? `data:image/jpeg;${logo}` : logoImg;
    // Setting BrandName to a variable here is necessary to get the jest tests
    // passing.  Attempting to use BrandName in the template literal results
    // in failing tests.
    const brandName = BrandName;

    if (isAuthenticated) {
      return (<Redirect to="/" />);
    }

    return (
      <LoginPage
        brandImgSrc={logoSrc}
        brandImgAlt={alt || brandName}
        loginTitle={i18n._(t`Welcome to Ansible ${brandName}! Please Sign In.`)}
        textContent={loginInfo}
      >
        <LoginForm
          className={errorMessage && 'pf-m-error'}
          usernameLabel={i18n._(t`Username`)}
          passwordLabel={i18n._(t`Password`)}
          showHelperText={!isInputValid || !!errorMessage}
          helperText={errorMessage || i18n._(t`Invalid username or password. Please try again.`)}
          usernameValue={username}
          passwordValue={password}
          isValidUsername={isInputValid}
          isValidPassword={isInputValid}
          onChangeUsername={this.onChangeUsername}
          onChangePassword={this.onChangePassword}
          onLoginButtonClick={this.onLoginButtonClick}
        />
      </LoginPage>
    );
  }
}

export { AWXLogin as _AWXLogin };
export default withI18n()(withNetwork(withRootDialog(withRouter(AWXLogin))));
