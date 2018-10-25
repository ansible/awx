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

  // initially renders empty username and password fields, sets empty error message and makes submit button not disabled

  // typing into username and password fields (if the component is not unmounting) will clear out any error message

  // when the submit Button is clicked, as long as it is not disabled state.loading is set to true
  // api.login is called with param 1 username and param 2 password
  // if api.login returns an error, the state.error should be set to LOGIN_ERROR_MESSAGE, if the error object returned has response.status set to 401.
  // regardless of error or not, after api.login returns, state.loading should be set to false

  // if api.isAuthenticated mock returns true, Redirect to / should be rendered
});