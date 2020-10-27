import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import mockAllSettings from '../../shared/data.allSettings.json';
import { SettingsProvider } from '../../../../contexts/Settings';
import { SettingsAPI } from '../../../../api';
import MiscSystemEdit from './MiscSystemEdit';

jest.mock('../../../../api/models/Settings');
SettingsAPI.updateAll.mockResolvedValue({});
SettingsAPI.readCategory.mockResolvedValue({
  data: mockAllSettings,
});
describe('<MiscSystemEdit />', () => {
  let wrapper;
  let history;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/settings/miscellaneous_system/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <MiscSystemEdit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('MiscSystemEdit').length).toBe(1);
  });

  test('should successfully send default values to api on form revert all', async () => {
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(0);
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
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
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
      '/settings/miscellaneous_system/details'
    );
  });

  test('should navigate to miscellaneous detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/settings/miscellaneous_system/details'
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
          <MiscSystemEdit />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
