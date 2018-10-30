import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount, shallow } from 'enzyme';
import LoginPage from '../../src/pages/Login';
import api from '../../src/api';

const LOGIN_ERROR_MESSAGE = 'Invalid username or password. Please try again.';

describe('<LoginPage />', () => {
  let loginWrapper;
  let loginPage;
  let loginForm;
  let usernameInput;
  let passwordInput;
  let errorTextArea;
  let submitButton;
  let defaultLogo;

  const findChildren = () => {
    loginPage = loginWrapper.find('LoginPage');
    loginForm = loginWrapper.find('form.pf-c-form');
    usernameInput = loginWrapper.find('.pf-c-form__group#username TextInput');
    passwordInput = loginWrapper.find('.pf-c-form__group#password TextInput');
    errorTextArea = loginWrapper.find('.pf-c-form__helper-text.pf-m-error');
    submitButton = loginWrapper.find('Button[type="submit"]');
    defaultLogo = loginWrapper.find('TowerLogo');
  };

  beforeEach(() => {
    loginWrapper = mount(<MemoryRouter><LoginPage /></MemoryRouter>);
    findChildren();
  });

  afterEach(() => {
    loginWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(loginWrapper.length).toBe(1);
    expect(loginForm.length).toBe(1);
    expect(usernameInput.length).toBe(1);
    expect(usernameInput.props().value).toBe('');
    expect(passwordInput.length).toBe(1);
    expect(passwordInput.props().value).toBe('');
    expect(errorTextArea.length).toBe(1);
    expect(loginPage.state().error).toBe('');
    expect(submitButton.length).toBe(1);
    expect(submitButton.props().isDisabled).toBe(false);
    expect(defaultLogo.length).toBe(1);
  });

  test('custom logo renders Brand component', () => {
    loginWrapper = mount(<MemoryRouter><LoginPage logo="hey" /></MemoryRouter>);
    findChildren();
    expect(defaultLogo.length).toBe(0);
  });

  test('state maps to un/pw input value props', () => {
    loginPage.setState({ username: 'un', password: 'pw' });
    expect(loginPage.state().username).toBe('un');
    expect(loginPage.state().password).toBe('pw');
    findChildren();
    expect(usernameInput.props().value).toBe('un');
    expect(passwordInput.props().value).toBe('pw');
  });

  test('updating un/pw clears out error', () => {
    loginPage.setState({ error: 'error!' });
    usernameInput.instance().props.onChange('uname');
    expect(loginPage.state().username).toBe('uname');
    expect(loginPage.state().error).toBe('');
    loginPage.setState({ error: 'error!' });
    passwordInput.instance().props.onChange('pword');
    expect(loginPage.state().password).toBe('pword');
    expect(loginPage.state().error).toBe('');
  });

  test('submit calls api.login successfully', (done) => {
    api.login = jest.fn().mockImplementation(() => {
      const loginPromise = Promise.resolve({});

      // wrapped in timeout so this .then happens after state.loading is set to
      // false in the actual .then handler
      //
      // would be improved by using .finally but that's not available for
      // some reason
      setTimeout(() => {
        loginPromise.then(() => {
          expect(loginPage.state().loading).toBe(false);
          done();
        });
      }, 50);

      return loginPromise;
    });
    expect(loginPage.state().loading).toBe(false);
    loginPage.setState({ username: 'unamee', password: 'pwordd', loading: true });
    submitButton.simulate('submit');
    expect(api.login).toHaveBeenCalledTimes(0);
    loginPage.setState({ loading: false });
    submitButton.simulate('submit');
    expect(api.login).toHaveBeenCalledTimes(1);
    expect(api.login).toHaveBeenCalledWith('unamee', 'pwordd');
    expect(loginPage.state().loading).toBe(true);
  });

  test('submit calls api.login handles 401 error', (done) => {
    api.login = jest.fn().mockImplementation(() => {
      const err = {
        response: { status: 401, message: 'problem' },
      };

      const loginPromise = Promise.reject(err);

      // wrapped in timeout so this .then happens after state.loading is set to
      // false in the actual .then handler
      //
      // would be improved by using .finally but that's not available for
      // some reason
      setTimeout(() => {
        loginPromise.catch(() => {
          expect(loginPage.state().loading).toBe(false);
          expect(loginPage.state().error).toBe(LOGIN_ERROR_MESSAGE);
          done();
        });
      }, 50);

      return loginPromise;
    });
    expect(loginPage.state().loading).toBe(false);
    loginPage.setState({ username: 'unamee', password: 'pwordd', loading: true });
    submitButton.simulate('submit');
    expect(api.login).toHaveBeenCalledTimes(0);
    loginPage.setState({ loading: false });
    expect(loginPage.state().error).toBe('');
    submitButton.simulate('submit');
    expect(api.login).toHaveBeenCalledTimes(1);
    expect(api.login).toHaveBeenCalledWith('unamee', 'pwordd');
    expect(loginPage.state().loading).toBe(true);
  });

  test('submit calls api.login handles 401 error', (done) => {
    api.login = jest.fn().mockImplementation(() => {
      const err = {
        response: { status: 500, message: 'problem' },
      };

      const loginPromise = Promise.reject(err);

      // wrapped in timeout so this .then happens after state.loading is set to
      // false in the actual .then handler
      //
      // would be improved by using .finally but that's not available for
      // some reason
      setTimeout(() => {
        loginPromise.catch(() => {
          expect(loginPage.state().loading).toBe(false);
          expect(loginPage.state().error).toBe('');
          done();
        });
      }, 50);

      return loginPromise;
    });
    expect(loginPage.state().loading).toBe(false);
    loginPage.setState({ username: 'unamee', password: 'pwordd', loading: true });
    submitButton.simulate('submit');
    expect(api.login).toHaveBeenCalledTimes(0);
    loginPage.setState({ loading: false });
    expect(loginPage.state().error).toBe('');
    submitButton.simulate('submit');
    expect(api.login).toHaveBeenCalledTimes(1);
    expect(api.login).toHaveBeenCalledWith('unamee', 'pwordd');
    expect(loginPage.state().loading).toBe(true);
  });

  test('render Redirect to / when already authenticated', () => {
    api.isAuthenticated = jest.fn();
    api.isAuthenticated.mockReturnValue(true);
    loginWrapper = shallow(<LoginPage />);
    const redirectElem = loginWrapper.find('Redirect');
    expect(redirectElem.length).toBe(1);
    expect(redirectElem.props().to).toBe('/');
  });
});
