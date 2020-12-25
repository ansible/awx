import React from 'react';
import { act } from 'react-dom/test-utils';
import { AuthAPI, RootAPI } from '../../api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../testUtils/enzymeHelpers';

import AWXLogin from './Login';

jest.mock('../../api');

RootAPI.readAssetVariables.mockResolvedValue({
  data: {
    BRAND_NAME: 'AWX',
  },
});

AuthAPI.read.mockResolvedValue({
  data: {},
});

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
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AWXLogin isAuthenticated={() => false} />);
    });
    const { usernameInput, passwordInput, submitButton } = await findChildren(
      wrapper
    );
    expect(usernameInput.props().value).toBe('');
    expect(passwordInput.props().value).toBe('');
    expect(submitButton.props().isDisabled).toBe(false);
    expect(wrapper.find('AlertModal').length).toBe(0);
    done();
  });

  test('custom logo renders Brand component with correct src and alt', async done => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(
        <AWXLogin alt="Foo Application" isAuthenticated={() => false} />
      );
    });
    const { loginHeaderLogo } = await findChildren(wrapper);
    const { alt, src } = loginHeaderLogo.props();
    expect([alt, src]).toEqual([
      'Foo Application',
      'data:image/jpeg;images/foo.jpg',
    ]);
    done();
  });

  test('default logo renders Brand component with correct src and alt', async done => {
    RootAPI.read.mockResolvedValue({ data: {} });
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AWXLogin isAuthenticated={() => false} />);
    });
    const { loginHeaderLogo } = await findChildren(wrapper);
    const { alt, src } = loginHeaderLogo.props();
    expect([alt, src]).toEqual(['AWX', '/static/media/logo-login.svg']);
    done();
  });

  test('data initialization error is properly handled', async done => {
    RootAPI.read.mockRejectedValueOnce(
      new Error({
        response: {
          config: {
            method: 'get',
            url: '/api/v2',
          },
          data: 'An error occurred',
          status: 500,
        },
      })
    );
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AWXLogin isAuthenticated={() => false} />);
    });
    const { loginHeaderLogo } = await findChildren(wrapper);
    const { alt, src } = loginHeaderLogo.props();
    expect([alt, src]).toEqual([null, '/static/media/logo-login.svg']);
    expect(wrapper.find('AlertModal').length).toBe(1);
    done();
  });

  test('state maps to un/pw input value props', async done => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AWXLogin isAuthenticated={() => false} />);
    });
    await waitForElement(wrapper, 'LoginForm', el => el.length === 1);
    await act(async () => {
      wrapper.find('TextInputBase#pf-login-username-id').prop('onChange')('un');
      wrapper.find('TextInputBase#pf-login-password-id').prop('onChange')('pw');
    });
    wrapper.update();
    expect(
      wrapper.find('TextInputBase#pf-login-username-id').prop('value')
    ).toEqual('un');
    expect(
      wrapper.find('TextInputBase#pf-login-password-id').prop('value')
    ).toEqual('pw');
    done();
  });

  test('handles input validation errors and clears on input value change', async done => {
    RootAPI.login.mockRejectedValueOnce(
      new Error({
        response: {
          config: {
            method: 'post',
            url: '/api/login/',
          },
          data: 'An error occurred',
          status: 401,
        },
      })
    );

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AWXLogin isAuthenticated={() => false} />);
    });
    await waitForElement(wrapper, 'LoginForm', el => el.length === 1);

    expect(
      wrapper.find('TextInputBase#pf-login-username-id').prop('value')
    ).toEqual('');
    expect(
      wrapper.find('TextInputBase#pf-login-password-id').prop('value')
    ).toEqual('');
    expect(wrapper.find('FormHelperText').prop('isHidden')).toEqual(true);

    await act(async () => {
      wrapper.find('TextInputBase#pf-login-username-id').prop('onChange')('un');
      wrapper.find('TextInputBase#pf-login-password-id').prop('onChange')('pw');
    });
    wrapper.update();

    expect(
      wrapper.find('TextInputBase#pf-login-username-id').prop('value')
    ).toEqual('un');
    expect(
      wrapper.find('TextInputBase#pf-login-password-id').prop('value')
    ).toEqual('pw');

    await act(async () => {
      wrapper.find('Button[type="submit"]').invoke('onClick')();
    });
    wrapper.update();

    expect(wrapper.find('FormHelperText').prop('isHidden')).toEqual(false);
    expect(
      wrapper.find('TextInput#pf-login-username-id').prop('validated')
    ).toEqual('error');
    expect(
      wrapper.find('TextInput#pf-login-password-id').prop('validated')
    ).toEqual('error');

    await act(async () => {
      wrapper.find('TextInputBase#pf-login-username-id').prop('onChange')(
        'foo'
      );
      wrapper.find('TextInputBase#pf-login-password-id').prop('onChange')(
        'bar'
      );
    });
    wrapper.update();

    expect(
      wrapper.find('TextInputBase#pf-login-username-id').prop('value')
    ).toEqual('foo');
    expect(
      wrapper.find('TextInputBase#pf-login-password-id').prop('value')
    ).toEqual('bar');
    expect(wrapper.find('FormHelperText').prop('isHidden')).toEqual(true);
    expect(
      wrapper.find('TextInput#pf-login-username-id').prop('validated')
    ).toEqual('default');
    expect(
      wrapper.find('TextInput#pf-login-password-id').prop('validated')
    ).toEqual('default');

    done();
  });

  test('submit calls api.login successfully', async done => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AWXLogin isAuthenticated={() => false} />);
    });
    await waitForElement(wrapper, 'LoginForm', el => el.length === 1);

    await act(async () => {
      wrapper.find('TextInputBase#pf-login-username-id').prop('onChange')('un');
      wrapper.find('TextInputBase#pf-login-password-id').prop('onChange')('pw');
    });
    wrapper.update();

    await act(async () => {
      wrapper.find('Button[type="submit"]').invoke('onClick')();
    });
    wrapper.update();

    expect(RootAPI.login).toHaveBeenCalledTimes(1);
    expect(RootAPI.login).toHaveBeenCalledWith('un', 'pw');

    done();
  });

  test('render Redirect to / when already authenticated', async done => {
    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AWXLogin isAuthenticated={() => true} />);
    });
    await waitForElement(wrapper, 'Redirect', el => el.length === 1);
    await waitForElement(wrapper, 'Redirect', el => el.props().to === '/');
    done();
  });

  test('GitHub auth buttons shown', async done => {
    AuthAPI.read.mockResolvedValue({
      data: {
        github: {
          login_url: '/sso/login/github/',
          complete_url: 'https://localhost:8043/sso/complete/github/',
        },
        'github-org': {
          login_url: '/sso/login/github-org/',
          complete_url: 'https://localhost:8043/sso/complete/github-org/',
        },
        'github-team': {
          login_url: '/sso/login/github-team/',
          complete_url: 'https://localhost:8043/sso/complete/github-team/',
        },
      },
    });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AWXLogin isAuthenticated={() => false} />);
    });
    wrapper.update();
    expect(wrapper.find('GithubIcon').length).toBe(3);
    expect(wrapper.find('AzureIcon').length).toBe(0);
    expect(wrapper.find('GoogleIcon').length).toBe(0);
    expect(wrapper.find('UserCircleIcon').length).toBe(0);
    done();
  });

  test('Google auth button shown', async done => {
    AuthAPI.read.mockResolvedValue({
      data: {
        'google-oauth2': {
          login_url: '/sso/login/google-oauth2/',
          complete_url: 'https://localhost:8043/sso/complete/google-oauth2/',
        },
      },
    });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AWXLogin isAuthenticated={() => false} />);
    });
    wrapper.update();
    expect(wrapper.find('GithubIcon').length).toBe(0);
    expect(wrapper.find('AzureIcon').length).toBe(0);
    expect(wrapper.find('GoogleIcon').length).toBe(1);
    expect(wrapper.find('UserCircleIcon').length).toBe(0);
    done();
  });

  test('Azure AD auth button shown', async done => {
    AuthAPI.read.mockResolvedValue({
      data: {
        'azuread-oauth2': {
          login_url: '/sso/login/azuread-oauth2/',
          complete_url: 'https://localhost:8043/sso/complete/azuread-oauth2/',
        },
      },
    });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AWXLogin isAuthenticated={() => false} />);
    });
    wrapper.update();
    expect(wrapper.find('GithubIcon').length).toBe(0);
    expect(wrapper.find('AzureIcon').length).toBe(1);
    expect(wrapper.find('GoogleIcon').length).toBe(0);
    expect(wrapper.find('UserCircleIcon').length).toBe(0);
    done();
  });

  test('SAML auth buttons shown', async done => {
    AuthAPI.read.mockResolvedValue({
      data: {
        saml: {
          login_url: '/sso/login/saml/',
          complete_url: 'https://localhost:8043/sso/complete/saml/',
          metadata_url: '/sso/metadata/saml/',
        },
        'saml:onelogin': {
          login_url: '/sso/login/saml/?idp=onelogin',
          complete_url: 'https://localhost:8043/sso/complete/saml/',
          metadata_url: '/sso/metadata/saml/',
        },
        'saml:someotheridp': {
          login_url: '/sso/login/saml/?idp=someotheridp',
          complete_url: 'https://localhost:8043/sso/complete/saml/',
          metadata_url: '/sso/metadata/saml/',
        },
      },
    });

    let wrapper;
    await act(async () => {
      wrapper = mountWithContexts(<AWXLogin isAuthenticated={() => false} />);
    });
    wrapper.update();
    expect(wrapper.find('GithubIcon').length).toBe(0);
    expect(wrapper.find('AzureIcon').length).toBe(0);
    expect(wrapper.find('GoogleIcon').length).toBe(0);
    expect(wrapper.find('UserCircleIcon').length).toBe(3);
    done();
  });
});
