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
    	.then(() => this.setState({ redirect: true }))
    	.then(() => api.getProjects())
    	.then(res => console.log(res));
  };

  render() {
    const { username, password, redirect } = this.state;

	if (redirect) {
		return (<Redirect to={'/'} />);
	}
  
    return (
      <div className='column'>
        <form onSubmit={this.handleSubmit}>
          <div className='field'>
            <label className='label'>Username</label>
            <div className='control'>
              <input
                className='input'
                type='text'
                name='username'
                onChange={this.handleChange}
                value={username}
                required
              />
            </div>
          </div>
          <div className='field'>
            <label className='label'>Password</label>
            <div className='control'>
              <input
                className='input'
                type='password'
                name='password'
                onChange={this.handleChange}
                value={password}
                required
              />
            </div>
          </div>
          <div className='control'>
            <Button type='submit'>
              Login
            </Button>
          </div>
        </form>
      </div>
    );
  }
}

export default Login;
