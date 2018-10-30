import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';
import {
  Brand,
  Button,
  Level,
  LevelItem,
  Login,
  LoginBox,
  LoginBoxHeader,
  LoginBoxBody,
  LoginFooter,
  LoginHeaderBrand,
  TextInput,
} from '@patternfly/react-core';

import TowerLogo from '../components/TowerLogo';
import api from '../api';

const LOGIN_ERROR_MESSAGE = 'Invalid username or password. Please try again.';

class LoginPage extends Component {
  constructor (props) {
    super(props);

    this.state = {
      username: '',
      password: '',
      error: '',
      loading: false,
    };
  }

  componentWillUnmount () {
    this.unmounting = true; // todo: state management
  }

  safeSetState = obj => !this.unmounting && this.setState(obj);

  handleUsernameChange = value => this.safeSetState({ username: value, error: '' });

  handlePasswordChange = value => this.safeSetState({ password: value, error: '' });

  handleSubmit = event => {
    const { username, password, loading } = this.state;

    event.preventDefault();

    if (!loading) {
      this.safeSetState({ loading: true });

      api.login(username, password)
        .then(() => {
          this.safeSetState({ loading: false });
        })
        .catch(error => {
          this.safeSetState({ loading: false });
          if (error.response.status === 401) {
            this.safeSetState({ error: LOGIN_ERROR_MESSAGE });
          }
        });
    }
  }

  render () {
    const { username, password, loading, error } = this.state;
    const { logo, loginInfo } = this.props;

    if (api.isAuthenticated()) {
      return (<Redirect to="/" />);
    }

    return (
      <Login
        header={(
          <LoginHeaderBrand>
            {logo ? <Brand src={`data:image/jpeg;${logo}`} alt="logo brand" /> : <TowerLogo />}
          </LoginHeaderBrand>
        )}
        footer={<LoginFooter>{ loginInfo }</LoginFooter>}
      >
        <LoginBox>
          <LoginBoxHeader>
            Welcome to Ansible Tower! Please Sign In.
          </LoginBoxHeader>
          <LoginBoxBody>
            <form className="pf-c-form" onSubmit={this.handleSubmit}>
              <div className="pf-c-form__group" id="username">
                <label className="pf-c-form__label" htmlFor="username">
                  Username
                  <span className="pf-c-form__label__required" aria-hidden="true">&#42;</span>
                </label>
                <TextInput
                  autoComplete="off"
                  aria-label="Username"
                  name="username"
                  type="text"
                  isDisabled={loading}
                  value={username}
                  onChange={this.handleUsernameChange}
                />
              </div>
              <div className="pf-c-form__group" id="password">
                <label className="pf-c-form__label" htmlFor="pw">
                  Password
                  <span className="pf-c-form__label__required" aria-hidden="true">&#42;</span>
                </label>
                <TextInput
                  aria-label="Password"
                  name="password"
                  type="password"
                  isDisabled={loading}
                  value={password}
                  onChange={this.handlePasswordChange}
                />
              </div>
              <Level>
                <LevelItem>
                  <p className="pf-c-form__helper-text pf-m-error" aria-live="polite">
                    { error }
                  </p>
                </LevelItem>
                <LevelItem>
                  <Button type="submit" isDisabled={loading}>
                    Sign In
                  </Button>
                </LevelItem>
              </Level>
            </form>
          </LoginBoxBody>
        </LoginBox>
      </Login>
    );
  }
}

export default LoginPage;
