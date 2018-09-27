import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';

import {
  Bullseye,
  Button,
  TextInput
} from '@patternfly/react-core';

import api from '../api';

class Login extends Component {
  state = {
    username: '',
    password: '',
    redirect: false,
  };

  handleUsernameChange = value => this.setState({ username: value });

  handlePasswordChange = value => this.setState({ password: value });

  handleSubmit = event => {
    const { username, password } = this.state;

    event.preventDefault();

    api.login(username, password)
      .then(() => this.setState({ redirect: true }));
  }

  render () {
    const { username, password, redirect } = this.state;

    if (redirect) {
      return (<Redirect to="/" />);
    }

    return (
      <Bullseye>
        <form onSubmit={this.handleSubmit}>
          <div>
            <TextInput
              aria-label="Username"
              name="username"
              type="text"
              onChange={this.handleUsernameChange}
              value={username}
            />
          </div>
          <div>
            <TextInput
              aria-label="Password"
              name="password"
              type="password"
              onChange={this.handlePasswordChange}
              value={password}
            />
          </div>
          <Button type="submit">
            Login
          </Button>
        </form>
      </Bullseye>
    );
  }
}

export default Login;
