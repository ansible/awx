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
import OIDCEdit from './OIDCEdit';

jest.mock('../../../../api');

describe('<OIDCEdit />', () => {
  let wrapper;
  let history;

  beforeEach(() => {
    SettingsAPI.revertCategory.mockResolvedValue({});
    SettingsAPI.updateAll.mockResolvedValue({});
    SettingsAPI.readCategory.mockResolvedValue({
      data: {
        SOCIAL_AUTH_OIDC_KEY: 'mock key',
        SOCIAL_AUTH_OIDC_SECRET: '$encrypted$',
        SOCIAL_AUTH_OIDC_OIDC_ENDPOINT: 'https://example.com',
        SOCIAL_AUTH_OIDC_VERIFY_SSL: true,
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/settings/oidc/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <OIDCEdit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('OIDCEdit').length).toBe(1);
  });

  test('should display expected form fields', async () => {
    expect(wrapper.find('FormGroup[label="OIDC Key"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="OIDC Secret"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="OIDC Provider URL"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="Verify OIDC Provider Certificate"]').length
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
    expect(SettingsAPI.revertCategory).toHaveBeenCalledWith('oidc');
  });

  test('should successfully send request to api on form submission', async () => {
    act(() => {
      wrapper
        .find(
          'FormGroup[fieldId="SOCIAL_AUTH_OIDC_SECRET"] button[aria-label="Revert"]'
        )
        .invoke('onClick')();
      wrapper.find('input#SOCIAL_AUTH_OIDC_KEY').simulate('change', {
        target: { value: 'new key', name: 'SOCIAL_AUTH_OIDC_KEY' },
      });
      wrapper.find('input#SOCIAL_AUTH_OIDC_OIDC_ENDPOINT').simulate('change', {
        target: {
          value: 'https://example.com',
          name: 'SOCIAL_AUTH_OIDC_OIDC_ENDPOINT',
        },
      });
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith({
      SOCIAL_AUTH_OIDC_KEY: 'new key',
      SOCIAL_AUTH_OIDC_SECRET: '',
      SOCIAL_AUTH_OIDC_OIDC_ENDPOINT: 'https://example.com',
      SOCIAL_AUTH_OIDC_VERIFY_SSL: true,
    });
  });

  test('should navigate to OIDC detail on successful submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(history.location.pathname).toEqual('/settings/oidc/details');
  });

  test('should navigate to OIDC detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual('/settings/oidc/details');
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
          <OIDCEdit />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
