import React, { Component } from 'react';
import { Redirect } from 'react-router-dom';

import { Button } from '@patternfly/react-core';

import api from '../api';

class Login extends Component {
  state = {
    username: '',
    password: '',
    redirect: false,
  };

  handleChange = event => this.setState({ [event.target.name]: event.target.value });

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
      <form onSubmit={this.handleSubmit}>
        <div className="field">
          <label htmlFor="username">
            Username
            <input
              id="username"
              name="username"
              type="text"
              onChange={this.handleChange}
              value={username}
            />
          </label>
        </div>
        <div>
          <label htmlFor="password">
            Password
            <input
              id="password"
              name="password"
              type="password"
              onChange={this.handleChange}
              value={password}
            />
          </label>
        </div>
        <Button type="submit">
          Login
        </Button>
      </form>
    );
  }
}

export default Login;
