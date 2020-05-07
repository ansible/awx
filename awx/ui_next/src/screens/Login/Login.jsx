import React, { Component } from 'react';
import { Redirect, withRouter } from 'react-router-dom';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { LoginForm, LoginPage as PFLoginPage } from '@patternfly/react-core';
import { RootAPI } from '../../api';
import { BrandName } from '../../variables';

import brandLogo from './brand-logo.svg';

const LoginPage = styled(PFLoginPage)`
  & .pf-c-brand {
    max-height: 285px;
  }
`;

class AWXLogin extends Component {
  constructor(props) {
    super(props);

    this.state = {
      username: '',
      password: '',
      hasAuthError: false,
      hasValidationError: false,
      isAuthenticating: false,
      isLoading: true,
      logo: null,
      loginInfo: null,
    };

    this.handleChangeUsername = this.handleChangeUsername.bind(this);
    this.handleChangePassword = this.handleChangePassword.bind(this);
    this.handleLoginButtonClick = this.handleLoginButtonClick.bind(this);
    this.loadCustomLoginInfo = this.loadCustomLoginInfo.bind(this);
  }

  async componentDidMount() {
    await this.loadCustomLoginInfo();
  }

  async loadCustomLoginInfo() {
    this.setState({ isLoading: true });
    try {
      const {
        data: { custom_logo, custom_login_info },
      } = await RootAPI.read();
      const logo = custom_logo ? `data:image/jpeg;${custom_logo}` : brandLogo;

      this.setState({ logo, loginInfo: custom_login_info });
    } catch (err) {
      this.setState({ logo: brandLogo });
    } finally {
      this.setState({ isLoading: false });
    }
  }

  async handleLoginButtonClick(event) {
    const { username, password, isAuthenticating } = this.state;

    event.preventDefault();

    if (isAuthenticating) {
      return;
    }

    this.setState({ hasAuthError: false, isAuthenticating: true });
    try {
      // note: if authentication is successful, the appropriate cookie will be set automatically
      // and isAuthenticated() (the source of truth) will start returning true.
      await RootAPI.login(username, password);
    } catch (err) {
      if (err && err.response && err.response.status === 401) {
        this.setState({ hasValidationError: true });
      } else {
        this.setState({ hasAuthError: true });
      }
    } finally {
      this.setState({ isAuthenticating: false });
    }
  }

  handleChangeUsername(value) {
    this.setState({ username: value, hasValidationError: false });
  }

  handleChangePassword(value) {
    this.setState({ password: value, hasValidationError: false });
  }

  render() {
    const {
      hasAuthError,
      hasValidationError,
      username,
      password,
      isLoading,
      logo,
      loginInfo,
    } = this.state;
    const { alt, i18n, isAuthenticated } = this.props;
    // Setting BrandName to a variable here is necessary to get the jest tests
    // passing.  Attempting to use BrandName in the template literal results
    // in failing tests.
    const brandName = BrandName;

    if (isLoading) {
      return null;
    }

    if (isAuthenticated(document.cookie)) {
      return <Redirect to="/" />;
    }

    let helperText;
    if (hasValidationError) {
      helperText = i18n._(t`Invalid username or password. Please try again.`);
    } else {
      helperText = i18n._(t`There was a problem signing in. Please try again.`);
    }

    return (
      <LoginPage
        brandImgSrc={logo}
        brandImgAlt={alt || brandName}
        loginTitle={i18n._(t`Welcome to Ansible ${brandName}! Please Sign In.`)}
        textContent={loginInfo}
      >
        <LoginForm
          className={hasAuthError || hasValidationError ? 'pf-m-error' : ''}
          helperText={helperText}
          isValidPassword={!hasValidationError}
          isValidUsername={!hasValidationError}
          loginButtonLabel={i18n._(t`Log In`)}
          onChangePassword={this.handleChangePassword}
          onChangeUsername={this.handleChangeUsername}
          onLoginButtonClick={this.handleLoginButtonClick}
          passwordLabel={i18n._(t`Password`)}
          passwordValue={password}
          showHelperText={hasAuthError || hasValidationError}
          usernameLabel={i18n._(t`Username`)}
          usernameValue={username}
        />
      </LoginPage>
    );
  }
}

export { AWXLogin as _AWXLogin };
export default withI18n()(withRouter(AWXLogin));
