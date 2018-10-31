import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount, shallow } from 'enzyme';
import { asyncFlush } from '../../jest.setup';
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

  test('api.login not called when loading', () => {
    api.login = jest.fn().mockImplementation(() => Promise.resolve({}));
    expect(loginPage.state().loading).toBe(false);
    loginPage.setState({ loading: true });
    submitButton.simulate('submit');
    expect(api.login).toHaveBeenCalledTimes(0);
  });

  test('submit calls api.login successfully', async () => {
    api.login = jest.fn().mockImplementation(() => Promise.resolve({}));
    expect(loginPage.state().loading).toBe(false);
    loginPage.setState({ username: 'unamee', password: 'pwordd' });
    submitButton.simulate('submit');
    expect(api.login).toHaveBeenCalledTimes(1);
    expect(api.login).toHaveBeenCalledWith('unamee', 'pwordd');
    expect(loginPage.state().loading).toBe(true);
    await asyncFlush();
    expect(loginPage.state().loading).toBe(false);
  });

  test('submit calls api.login handles 401 error', async () => {
    api.login = jest.fn().mockImplementation(() => {
      const err = new Error('401 error');
      err.response = { status: 401, message: 'problem' };
      return Promise.reject(err);
    });
    expect(loginPage.state().loading).toBe(false);
    loginPage.setState({ username: 'unamee', password: 'pwordd' });
    submitButton.simulate('submit');
    expect(api.login).toHaveBeenCalledTimes(1);
    expect(api.login).toHaveBeenCalledWith('unamee', 'pwordd');
    expect(loginPage.state().loading).toBe(true);
    await asyncFlush();
    expect(loginPage.state().error).toBe(LOGIN_ERROR_MESSAGE);
    expect(loginPage.state().loading).toBe(false);
  });

  test('submit calls api.login handles non-401 error', async () => {
    api.login = jest.fn().mockImplementation(() => {
      const err = new Error('500 error');
      err.response = { status: 500, message: 'problem' };
      return Promise.reject(err);
    });
    expect(loginPage.state().loading).toBe(false);
    loginPage.setState({ username: 'unamee', password: 'pwordd' });
    submitButton.simulate('submit');
    expect(api.login).toHaveBeenCalledTimes(1);
    expect(api.login).toHaveBeenCalledWith('unamee', 'pwordd');
    expect(loginPage.state().loading).toBe(true);
    await asyncFlush();
    expect(loginPage.state().error).toBe('');
    expect(loginPage.state().loading).toBe(false);
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
