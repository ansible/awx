import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { mount, shallow } from 'enzyme';
import { I18nProvider } from '@lingui/react';
import { asyncFlush } from '../../jest.setup';
import AWXLogin from '../../src/pages/Login';
import APIClient from '../../src/api';

describe('<Login />', () => {
  let loginWrapper;
  let awxLogin;
  let loginPage;
  let loginForm;
  let usernameInput;
  let passwordInput;
  let submitButton;
  let loginHeaderLogo;

  const api = new APIClient({});

  const findChildren = () => {
    awxLogin = loginWrapper.find('AWXLogin');
    loginPage = loginWrapper.find('LoginPage');
    loginForm = loginWrapper.find('LoginForm');
    usernameInput = loginWrapper.find('input#pf-login-username-id');
    passwordInput = loginWrapper.find('input#pf-login-password-id');
    submitButton = loginWrapper.find('Button[type="submit"]');
    loginHeaderLogo = loginPage.find('img');
  };

  beforeEach(() => {
    loginWrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <AWXLogin api={api} />
        </I18nProvider>
      </MemoryRouter>
    );
    findChildren();
  });

  afterEach(() => {
    loginWrapper.unmount();
  });

  test('initially renders without crashing', () => {
    expect(loginWrapper.length).toBe(1);
    expect(loginPage.length).toBe(1);
    expect(loginForm.length).toBe(1);
    expect(usernameInput.length).toBe(1);
    expect(usernameInput.props().value).toBe('');
    expect(passwordInput.length).toBe(1);
    expect(passwordInput.props().value).toBe('');
    expect(awxLogin.state().isInputValid).toBe(true);
    expect(submitButton.length).toBe(1);
    expect(submitButton.props().isDisabled).toBe(false);
    expect(loginHeaderLogo.length).toBe(1);
  });

  test('custom logo renders Brand component with correct src and alt', () => {
    loginWrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <AWXLogin api={api} logo="images/foo.jpg" alt="Foo Application" />
        </I18nProvider>
      </MemoryRouter>
    );
    findChildren();
    expect(loginHeaderLogo.length).toBe(1);
    expect(loginHeaderLogo.props().src).toBe('data:image/jpeg;images/foo.jpg');
    expect(loginHeaderLogo.props().alt).toBe('Foo Application');
  });

  test('default logo renders Brand component with correct src and alt', () => {
    loginWrapper = mount(
      <MemoryRouter>
        <I18nProvider>
          <AWXLogin api={api} />
        </I18nProvider>
      </MemoryRouter>
    );
    findChildren();
    expect(loginHeaderLogo.length).toBe(1);
    expect(loginHeaderLogo.props().src).toBe('tower-logo-header.svg');
    expect(loginHeaderLogo.props().alt).toBe('Ansible Tower');
  });

  test('state maps to un/pw input value props', () => {
    awxLogin.setState({ username: 'un', password: 'pw' });
    expect(awxLogin.state().username).toBe('un');
    expect(awxLogin.state().password).toBe('pw');
    findChildren();
    expect(usernameInput.props().value).toBe('un');
    expect(passwordInput.props().value).toBe('pw');
  });

  test('updating un/pw clears out error', () => {
    awxLogin.setState({ isInputValid: false });
    expect(loginWrapper.find('.pf-c-form__helper-text.pf-m-error').length).toBe(1);
    usernameInput.instance().value = 'uname';
    usernameInput.simulate('change');
    expect(awxLogin.state().username).toBe('uname');
    expect(awxLogin.state().isInputValid).toBe(true);
    expect(loginWrapper.find('.pf-c-form__helper-text.pf-m-error').length).toBe(0);
    awxLogin.setState({ isInputValid: false });
    expect(loginWrapper.find('.pf-c-form__helper-text.pf-m-error').length).toBe(1);
    passwordInput.instance().value = 'pword';
    passwordInput.simulate('change');
    expect(awxLogin.state().password).toBe('pword');
    expect(awxLogin.state().isInputValid).toBe(true);
    expect(loginWrapper.find('.pf-c-form__helper-text.pf-m-error').length).toBe(0);
  });

  test('api.login not called when loading', () => {
    api.login = jest.fn().mockImplementation(() => Promise.resolve({}));
    expect(awxLogin.state().isLoading).toBe(false);
    awxLogin.setState({ isLoading: true });
    submitButton.simulate('click');
    expect(api.login).toHaveBeenCalledTimes(0);
  });

  test('submit calls api.login successfully', async () => {
    api.login = jest.fn().mockImplementation(() => Promise.resolve({}));
    expect(awxLogin.state().isLoading).toBe(false);
    awxLogin.setState({ username: 'unamee', password: 'pwordd' });
    submitButton.simulate('click');
    expect(api.login).toHaveBeenCalledTimes(1);
    expect(api.login).toHaveBeenCalledWith('unamee', 'pwordd');
    expect(awxLogin.state().isLoading).toBe(true);
    await asyncFlush();
    expect(awxLogin.state().isLoading).toBe(false);
  });

  test('submit calls api.login handles 401 error', async () => {
    api.login = jest.fn().mockImplementation(() => {
      const err = new Error('401 error');
      err.response = { status: 401, message: 'problem' };
      return Promise.reject(err);
    });
    expect(awxLogin.state().isLoading).toBe(false);
    expect(awxLogin.state().isInputValid).toBe(true);
    awxLogin.setState({ username: 'unamee', password: 'pwordd' });
    submitButton.simulate('click');
    expect(api.login).toHaveBeenCalledTimes(1);
    expect(api.login).toHaveBeenCalledWith('unamee', 'pwordd');
    expect(awxLogin.state().isLoading).toBe(true);
    await asyncFlush();
    expect(awxLogin.state().isInputValid).toBe(false);
    expect(awxLogin.state().isLoading).toBe(false);
  });

  test('submit calls api.login handles non-401 error', async () => {
    api.login = jest.fn().mockImplementation(() => {
      const err = new Error('500 error');
      err.response = { status: 500, message: 'problem' };
      return Promise.reject(err);
    });
    expect(awxLogin.state().isLoading).toBe(false);
    awxLogin.setState({ username: 'unamee', password: 'pwordd' });
    submitButton.simulate('click');
    expect(api.login).toHaveBeenCalledTimes(1);
    expect(api.login).toHaveBeenCalledWith('unamee', 'pwordd');
    expect(awxLogin.state().isLoading).toBe(true);
    await asyncFlush();
    expect(awxLogin.state().isLoading).toBe(false);
  });

  test('render Redirect to / when already authenticated', () => {
    api.isAuthenticated = jest.fn();
    api.isAuthenticated.mockReturnValue(true);
    loginWrapper = shallow(<AWXLogin api={api} />);
    const redirectElem = loginWrapper.find('Redirect');
    expect(redirectElem.length).toBe(1);
    expect(redirectElem.props().to).toBe('/');
  });
});
