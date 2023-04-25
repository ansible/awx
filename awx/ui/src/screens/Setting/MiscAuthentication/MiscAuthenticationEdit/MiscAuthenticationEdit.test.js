import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import mockAllSettings from '../../shared/data.allSettings.json';
import MiscAuthenticationEdit from './MiscAuthenticationEdit';

jest.mock('../../../../api');

const authenticationData = {
  SESSION_COOKIE_AGE: 1800,
  SESSIONS_PER_USER: -1,
  DISABLE_LOCAL_AUTH: false,
  AUTH_BASIC_ENABLED: true,
  OAUTH2_PROVIDER: {
    ACCESS_TOKEN_EXPIRE_SECONDS: 31536000000,
    REFRESH_TOKEN_EXPIRE_SECONDS: 2628000,
    AUTHORIZATION_CODE_EXPIRE_SECONDS: 600,
  },
  ALLOW_OAUTH2_FOR_EXTERNAL_USERS: false,
  LOGIN_REDIRECT_OVERRIDE: '',
  AUTHENTICATION_BACKENDS: [
    'awx.sso.backends.TACACSPlusBackend',
    'awx.main.backends.AWXModelBackend',
  ],
  SOCIAL_AUTH_ORGANIZATION_MAP: null,
  SOCIAL_AUTH_TEAM_MAP: null,
  SOCIAL_AUTH_USER_FIELDS: null,
  SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL: false,
  LOCAL_PASSWORD_MIN_LENGTH: 0,
  LOCAL_PASSWORD_MIN_DIGITS: 0,
  LOCAL_PASSWORD_MIN_UPPER: 0,
  LOCAL_PASSWORD_MIN_SPECIAL: 0,
};

describe('<MiscAuthenticationEdit />', () => {
  let wrapper;
  let history;

  afterEach(() => {
    jest.clearAllMocks();
  });

  beforeEach(async () => {
    SettingsAPI.revertCategory.mockResolvedValue({});
    SettingsAPI.updateAll.mockResolvedValue({});
    SettingsAPI.readCategory.mockResolvedValue({
      data: mockAllSettings,
    });
    history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_authentication/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <MiscAuthenticationEdit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('should enable edit login redirect once alert is confirmed', async () => {
    expect(
      wrapper.find('TextInput#LOGIN_REDIRECT_OVERRIDE').prop('isDisabled')
    ).toBe(true);
    await act(async () =>
      wrapper
        .find('Button[ouiaId="confirm-edit-login-redirect"]')
        .simulate('click')
    );
    wrapper.update();
    const modal = wrapper.find('AlertModal');
    expect(modal).toHaveLength(1);
    expect(modal.prop('isOpen')).toEqual(true);
    await act(async () =>
      modal
        .find('Button[aria-label="confirm edit login redirect"]')
        .simulate('click')
    );
    wrapper.update();
    expect(
      wrapper.find('TextInput#LOGIN_REDIRECT_OVERRIDE').prop('isDisabled')
    ).toBe(false);

    await act(async () => {
      wrapper.find('TextInput#LOGIN_REDIRECT_OVERRIDE').invoke('onChange')(
        null,
        {
          target: {
            name: 'LOGIN_REDIRECT_OVERRIDE',
            value: 'bar',
          },
        }
      );
    });
    wrapper.update();
    expect(
      wrapper.find('TextInput#LOGIN_REDIRECT_OVERRIDE').prop('value')
    ).toEqual('bar');
  });

  test('initially renders without crashing', async () => {
    expect(wrapper.find('MiscAuthenticationEdit').length).toBe(1);
  });

  test('save button should call updateAll', async () => {
    expect(wrapper.find('MiscAuthenticationEdit').length).toBe(1);
    wrapper.update();
    await act(async () => {
      wrapper.find('button[aria-label="Save"]').simulate('click');
    });
    wrapper.update();
    const { AUTHENTICATION_BACKENDS, ...rest } = authenticationData;
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith(rest);
  });

  test('should successfully send default values to api on form revert all', async () => {
    expect(SettingsAPI.revertCategory).toHaveBeenCalledTimes(0);
    expect(wrapper.find('RevertAllAlert')).toHaveLength(0);
    await act(async () => {
      wrapper
        .find('button[aria-label="Revert all to default"]')
        .invoke('onClick')();
    });
    wrapper.update();
    expect(wrapper.find('RevertAllAlert')).toHaveLength(1);
    await act(async () => {
      wrapper
        .find('RevertAllAlert button[aria-label="Confirm revert all"]')
        .invoke('onClick')();
    });
    wrapper.update();
    expect(SettingsAPI.revertCategory).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.revertCategory).toHaveBeenCalledWith('authentication');
  });

  test('should successfully send request to api on form submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
  });

  test('should navigate to miscellaneous detail on successful submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(history.location.pathname).toEqual(
      '/settings/miscellaneous_authentication/details'
    );
  });

  test('should navigate to miscellaneous detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/settings/miscellaneous_authentication/details'
    );
  });

  test('should display error message on unsuccessful submission', async () => {
    const error = {
      response: {
        data: { detail: 'An error occurred' },
      },
    };
    SettingsAPI.updateAll.mockImplementation(() => Promise.reject(error));
    expect(wrapper.find('FormSubmitError').length).toBe(0);
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(0);
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    wrapper.update();
    expect(wrapper.find('FormSubmitError').length).toBe(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
  });

  test('should display ContentError on throw', async () => {
    SettingsAPI.readCategory.mockImplementationOnce(() =>
      Promise.reject(new Error())
    );
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <MiscAuthenticationEdit />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
