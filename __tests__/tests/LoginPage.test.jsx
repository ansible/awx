import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { shallow, mount } from 'enzyme';
import LoginPage from '../../src/pages/Login';
import api from '../../src/api';
import Dashboard from '../../src/pages/Dashboard';

describe('<LoginPage />', () => {
  let loginWrapper, usernameInput, passwordInput, errorTextArea, submitButton;

  beforeEach(() => {
    loginWrapper = mount(<MemoryRouter><LoginPage /></MemoryRouter>);
    usernameInput = loginWrapper.find('.pf-c-form__group#username TextInput');
    passwordInput = loginWrapper.find('.pf-c-form__group#password TextInput');
    errorTextArea = loginWrapper.find('.pf-c-form__helper-text.pf-m-error');
    submitButton = loginWrapper.find('Button[type="submit"]');
  });

  test('initially renders without crashing', () => {
    expect(loginWrapper.length).toBe(1);
    expect(usernameInput.length).toBe(1);
    expect(passwordInput.length).toBe(1);
    expect(errorTextArea.length).toBe(1);
    expect(submitButton.length).toBe(1);
  });

  // initially renders empty username and password fields
  // as well as state.username and state.password to empty strings
  // initially sets state.error and state.loading to false

  // on unmount, unmount is set to true

  // typing into username and password fields (if the component is not unmounting)
  // set state.username and state.password, as well as set state.error to empty string
  // this is done through the handleUsernameChange and handlePasswordChange functions
  // which both call safeSetState

  // when the submit Button is clicked, as long as it is not disabled (through state.loading
  // being set tp true), state.loading is set to true (through safeSetState)
  // api.login is called with param 1 username and param 2 password based on state
  
  // if api.login returns an error, the state.error should be set to LOGIN_ERROR_MESSAGE
  // if the error object returned has response.status set to 401.

  // regardless of error or not, after api.login returns state.loading should be set to false
  // via safeSetState

  // QUESTION: if api.login is valid, how does redirect happen?
});