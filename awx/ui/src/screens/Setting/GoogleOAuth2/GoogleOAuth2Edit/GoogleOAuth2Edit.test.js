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
import GoogleOAuth2Edit from './GoogleOAuth2Edit';

jest.mock('../../../../api');

describe('<GoogleOAuth2Edit />', () => {
  let wrapper;
  let history;

  beforeEach(() => {
    SettingsAPI.revertCategory.mockResolvedValue({});
    SettingsAPI.updateAll.mockResolvedValue({});
    SettingsAPI.readCategory.mockResolvedValue({
      data: {
        SOCIAL_AUTH_GOOGLE_OAUTH2_CALLBACK_URL:
          'https://towerhost/sso/complete/google-oauth2/',
        SOCIAL_AUTH_GOOGLE_OAUTH2_KEY: 'mock key',
        SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET: '$encrypted$',
        SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS: [
          'example.com',
          'example_2.com',
        ],
        SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS: {},
        SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP: {
          Default: {},
        },
        SOCIAL_AUTH_GOOGLE_OAUTH2_TEAM_MAP: {},
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/settings/google_oauth2/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <GoogleOAuth2Edit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('GoogleOAuth2Edit').length).toBe(1);
  });

  test('should display expected form fields', async () => {
    expect(wrapper.find('FormGroup[label="Google OAuth2 Key"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="Google OAuth2 Secret"]').length).toBe(
      1
    );
    expect(
      wrapper.find('FormGroup[label="Google OAuth2 Allowed Domains"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Google OAuth2 Extra Arguments"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Google OAuth2 Organization Map"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Google OAuth2 Team Map"]').length
    ).toBe(1);
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
    expect(SettingsAPI.revertCategory).toHaveBeenCalledWith('google-oauth2');
  });

  test('should successfully send request to api on form submission', async () => {
    act(() => {
      wrapper
        .find(
          'FormGroup[fieldId="SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS"] button[aria-label="Revert"]'
        )
        .invoke('onClick')();
      wrapper
        .find(
          'FormGroup[fieldId="SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET"] button[aria-label="Revert"]'
        )
        .invoke('onClick')();
      wrapper.find('input#SOCIAL_AUTH_GOOGLE_OAUTH2_KEY').simulate('change', {
        target: { value: 'new key', name: 'SOCIAL_AUTH_GOOGLE_OAUTH2_KEY' },
      });
      wrapper
        .find('CodeEditor#SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP')
        .invoke('onChange')('{\n"Default":{\n"users":\nfalse\n}\n}');
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith({
      SOCIAL_AUTH_GOOGLE_OAUTH2_KEY: 'new key',
      SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET: '',
      SOCIAL_AUTH_GOOGLE_OAUTH2_WHITELISTED_DOMAINS: [],
      SOCIAL_AUTH_GOOGLE_OAUTH2_AUTH_EXTRA_ARGUMENTS: {},
      SOCIAL_AUTH_GOOGLE_OAUTH2_TEAM_MAP: {},
      SOCIAL_AUTH_GOOGLE_OAUTH2_ORGANIZATION_MAP: {
        Default: {
          users: false,
        },
      },
    });
  });

  test('should navigate to Google OAuth 2.0 detail on successful submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(history.location.pathname).toEqual(
      '/settings/google_oauth2/details'
    );
  });

  test('should navigate to Google OAuth 2.0 detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/settings/google_oauth2/details'
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
          <GoogleOAuth2Edit />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
