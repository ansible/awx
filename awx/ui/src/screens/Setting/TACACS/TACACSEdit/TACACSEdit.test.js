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
import TACACSEdit from './TACACSEdit';

jest.mock('../../../../api/');

describe('<TACACSEdit />', () => {
  let wrapper;
  let history;

  beforeEach(() => {
    SettingsAPI.revertCategory.mockResolvedValue({});
    SettingsAPI.updateAll.mockResolvedValue({});
    SettingsAPI.readCategory.mockResolvedValue({
      data: {
        TACACSPLUS_HOST: 'mockhost',
        TACACSPLUS_PORT: 49,
        TACACSPLUS_SECRET: '$encrypted$',
        TACACSPLUS_SESSION_TIMEOUT: 123,
        TACACSPLUS_AUTH_PROTOCOL: 'ascii',
        TACACSPLUS_REM_ADDR: false,
      },
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/settings/tacacs/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <TACACSEdit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('TACACSEdit').length).toBe(1);
  });

  test('should display expected form fields', async () => {
    expect(wrapper.find('FormGroup[label="TACACS+ Server"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="TACACS+ Port"]').length).toBe(1);
    expect(wrapper.find('FormGroup[label="TACACS+ Secret"]').length).toBe(1);
    expect(
      wrapper.find('FormGroup[label="TACACS+ Auth Session Timeout"]').length
    ).toBe(1);
    expect(
      wrapper.find('FormGroup[label="TACACS+ Authentication Protocol"]').length
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
    expect(SettingsAPI.revertCategory).toHaveBeenCalledWith('tacacsplus');
  });

  test('should successfully send request to api on form submission', async () => {
    act(() => {
      wrapper.find('input#TACACSPLUS_HOST').simulate('change', {
        target: { value: 'new_host', name: 'TACACSPLUS_HOST' },
      });
      wrapper.find('input#TACACSPLUS_PORT').simulate('change', {
        target: { value: 999, name: 'TACACSPLUS_PORT' },
      });
      wrapper
        .find(
          'FormGroup[fieldId="TACACSPLUS_SECRET"] button[aria-label="Revert"]'
        )
        .invoke('onClick')();
    });
    wrapper.update();
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith({
      TACACSPLUS_HOST: 'new_host',
      TACACSPLUS_PORT: 999,
      TACACSPLUS_SECRET: '',
      TACACSPLUS_SESSION_TIMEOUT: 123,
      TACACSPLUS_AUTH_PROTOCOL: 'ascii',
      TACACSPLUS_REM_ADDR: false,
    });
  });

  test('should navigate to tacacs detail on successful submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(history.location.pathname).toEqual('/settings/tacacs/details');
  });

  test('should navigate to tacacs detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual('/settings/tacacs/details');
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
          <TACACSEdit />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
