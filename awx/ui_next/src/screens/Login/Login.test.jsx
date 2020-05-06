import React from 'react';

import { RootAPI } from '../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';

import AWXLogin from './Login';

jest.mock('../../api');

describe('<Login />', () => {
  async function findChildren(wrapper) {
    const [
      awxLogin,
      loginPage,
      loginForm,
      usernameInput,
      passwordInput,
      submitButton,
      loginHeaderLogo,
    ] = await Promise.all([
      waitForElement(wrapper, 'AWXLogin', el => el.length === 1),
      waitForElement(wrapper, 'LoginPage', el => el.length === 1),
      waitForElement(wrapper, 'LoginForm', el => el.length === 1),
      waitForElement(
        wrapper,
        'input#pf-login-username-id',
        el => el.length === 1
      ),
      waitForElement(
        wrapper,
        'input#pf-login-password-id',
        el => el.length === 1
      ),
      waitForElement(wrapper, 'Button[type="submit"]', el => el.length === 1),
      waitForElement(wrapper, 'img', el => el.length === 1),
    ]);
    return {
      awxLogin,
      loginPage,
      loginForm,
      usernameInput,
      passwordInput,
      submitButton,
      loginHeaderLogo,
    };
  }

  beforeEach(() => {
    RootAPI.read.mockResolvedValue({
      data: {
        custom_login_info: '',
        custom_logo: 'images/foo.jpg',
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('initially renders without crashing', async done => {
    const loginWrapper = mountWithContexts(
      <AWXLogin isAuthenticated={() => false} />
    );
    const {
      awxLogin,
      usernameInput,
      passwordInput,
      submitButton,
    } = await findChildren(loginWrapper);
    expect(usernameInput.props().value).toBe('');
    expect(passwordInput.props().value).toBe('');
    expect(awxLogin.state('hasValidationError')).toBe(false);
    expect(submitButton.props().isDisabled).toBe(false);
    done();
  });

  test('custom logo renders Brand component with correct src and alt', async done => {
    const loginWrapper = mountWithContexts(
      <AWXLogin alt="Foo Application" isAuthenticated={() => false} />
    );
    const { loginHeaderLogo } = await findChildren(loginWrapper);
    const { alt, src } = loginHeaderLogo.props();
    expect([alt, src]).toEqual([
      'Foo Application',
      'data:image/jpeg;images/foo.jpg',
    ]);
    done();
  });

  test('default logo renders Brand component with correct src and alt', async done => {
    RootAPI.read.mockResolvedValue({ data: {} });
    const loginWrapper = mountWithContexts(
      <AWXLogin isAuthenticated={() => false} />
    );
    const { loginHeaderLogo } = await findChildren(loginWrapper);
    const { alt, src } = loginHeaderLogo.props();
    expect([alt, src]).toEqual(['AWX', 'brand-logo.svg']);
    done();
  });

  test('default logo renders on data initialization error', async done => {
    RootAPI.read.mockRejectedValueOnce({ response: { status: 500 } });
    const loginWrapper = mountWithContexts(
      <AWXLogin isAuthenticated={() => false} />
    );
    const { loginHeaderLogo } = await findChildren(loginWrapper);
    const { alt, src } = loginHeaderLogo.props();
    expect([alt, src]).toEqual(['AWX', 'brand-logo.svg']);
    done();
  });

  test('state maps to un/pw input value props', async done => {
    const loginWrapper = mountWithContexts(
      <AWXLogin isAuthenticated={() => false} />
    );
    const { usernameInput, passwordInput } = await findChildren(loginWrapper);
    usernameInput.props().onChange({ currentTarget: { value: 'un' } });
    passwordInput.props().onChange({ currentTarget: { value: 'pw' } });
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('username') === 'un'
    );
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('password') === 'pw'
    );
    done();
  });

  test('handles input validation errors and clears on input value change', async done => {
    const formError = '.pf-c-form__helper-text.pf-m-error';
    const loginWrapper = mountWithContexts(
      <AWXLogin isAuthenticated={() => false} />
    );
    const { usernameInput, passwordInput, submitButton } = await findChildren(
      loginWrapper
    );

    RootAPI.login.mockRejectedValueOnce({ response: { status: 401 } });
    usernameInput.props().onChange({ currentTarget: { value: 'invalid' } });
    passwordInput.props().onChange({ currentTarget: { value: 'invalid' } });
    submitButton.simulate('click');
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('username') === 'invalid'
    );
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('password') === 'invalid'
    );
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('hasValidationError') === true
    );
    await waitForElement(loginWrapper, formError, el => el.length === 1);

    usernameInput.props().onChange({ currentTarget: { value: 'dsarif' } });
    passwordInput.props().onChange({ currentTarget: { value: 'freneticpny' } });
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('username') === 'dsarif'
    );
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('password') === 'freneticpny'
    );
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('hasValidationError') === false
    );
    await waitForElement(loginWrapper, formError, el => el.length === 0);

    done();
  });

  test('handles other errors and clears on resubmit', async done => {
    const loginWrapper = mountWithContexts(
      <AWXLogin isAuthenticated={() => false} />
    );
    const { usernameInput, passwordInput, submitButton } = await findChildren(
      loginWrapper
    );

    RootAPI.login.mockRejectedValueOnce({ response: { status: 500 } });
    submitButton.simulate('click');
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('hasAuthError') === true
    );

    usernameInput.props().onChange({ currentTarget: { value: 'sgrimes' } });
    passwordInput.props().onChange({ currentTarget: { value: 'ovid' } });
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('username') === 'sgrimes'
    );
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('password') === 'ovid'
    );
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('hasAuthError') === true
    );

    submitButton.simulate('click');
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('hasAuthError') === false
    );
    done();
  });

  test('no login requests are made when already authenticating', async done => {
    const loginWrapper = mountWithContexts(
      <AWXLogin isAuthenticated={() => false} />
    );
    const { awxLogin, submitButton } = await findChildren(loginWrapper);

    awxLogin.setState({ isAuthenticating: true });
    submitButton.simulate('click');
    submitButton.simulate('click');
    expect(RootAPI.login).toHaveBeenCalledTimes(0);

    awxLogin.setState({ isAuthenticating: false });
    submitButton.simulate('click');
    submitButton.simulate('click');
    expect(RootAPI.login).toHaveBeenCalledTimes(1);

    done();
  });

  test('submit calls api.login successfully', async done => {
    const loginWrapper = mountWithContexts(
      <AWXLogin isAuthenticated={() => false} />
    );
    const { usernameInput, passwordInput, submitButton } = await findChildren(
      loginWrapper
    );

    usernameInput.props().onChange({ currentTarget: { value: 'gthorpe' } });
    passwordInput.props().onChange({ currentTarget: { value: 'hydro' } });
    submitButton.simulate('click');
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('isAuthenticating') === true
    );
    await waitForElement(
      loginWrapper,
      'AWXLogin',
      el => el.state('isAuthenticating') === false
    );
    expect(RootAPI.login).toHaveBeenCalledTimes(1);
    expect(RootAPI.login).toHaveBeenCalledWith('gthorpe', 'hydro');

    done();
  });

  test('render Redirect to / when already authenticated', async done => {
    const loginWrapper = mountWithContexts(
      <AWXLogin isAuthenticated={() => true} />
    );
    await waitForElement(loginWrapper, 'Redirect', el => el.length === 1);
    await waitForElement(loginWrapper, 'Redirect', el => el.props().to === '/');
    done();
  });
});
