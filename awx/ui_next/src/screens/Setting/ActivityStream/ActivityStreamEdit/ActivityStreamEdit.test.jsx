import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import { SettingsProvider } from '../../../../contexts/Settings';
import { SettingsAPI } from '../../../../api';
import ActivityStreamEdit from './ActivityStreamEdit';

jest.mock('../../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {
    ACTIVITY_STREAM_ENABLED: false,
    ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC: true,
  },
});
SettingsAPI.updateAll.mockResolvedValue({});
describe('<ActivityStreamEdit />', () => {
  let wrapper;
  let history;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  beforeEach(async () => {
    history = createMemoryHistory({
      initialEntries: ['/settings/activity_stream/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <ActivityStreamEdit />
        </SettingsProvider>,
        {
          context: { router: { history } },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('ActivityStreamEdit').length).toBe(1);
  });

  test('should navigate to activity stream detail when cancel is clicked', async () => {
    await act(async () => {
      wrapper.find('button[aria-label="Cancel"]').invoke('onClick')();
    });
    expect(history.location.pathname).toEqual(
      '/settings/activity_stream/details'
    );
  });

  test('should navigate to activity stream detail on successful submission', async () => {
    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(history.location.pathname).toEqual(
      '/settings/activity_stream/details'
    );
  });

  test('should successfully send request to api on form submission', async () => {
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(0);
    expect(
      wrapper.find('Switch#ACTIVITY_STREAM_ENABLED').prop('isChecked')
    ).toEqual(false);

    await act(async () => {
      wrapper.find('Switch#ACTIVITY_STREAM_ENABLED').invoke('onChange')(true);
    });
    wrapper.update();
    expect(
      wrapper.find('Switch#ACTIVITY_STREAM_ENABLED').prop('isChecked')
    ).toEqual(true);

    await act(async () => {
      wrapper.find('Form').invoke('onSubmit')();
    });
    expect(SettingsAPI.updateAll).toHaveBeenCalledTimes(1);
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith({
      ACTIVITY_STREAM_ENABLED: true,
      ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC: true,
    });
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
    expect(SettingsAPI.updateAll).toHaveBeenCalledWith({
      ACTIVITY_STREAM_ENABLED: true,
      ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC: false,
    });
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
          <ActivityStreamEdit />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
