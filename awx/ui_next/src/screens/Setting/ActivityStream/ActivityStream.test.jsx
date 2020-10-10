import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import ActivityStream from './ActivityStream';
import { SettingsAPI } from '../../../api';

jest.mock('../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {
    ACTIVITY_STREAM_ENABLED: true,
    ACTIVITY_STREAM_ENABLED_FOR_INVENTORY_SYNC: false,
  },
});

describe('<ActivityStream />', () => {
  let wrapper;

  afterEach(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('should render activity stream details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/activity_stream/details'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<ActivityStream />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ActivityStreamDetail').length).toBe(1);
  });

  test('should render activity stream edit', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/activity_stream/edit'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<ActivityStream />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ActivityStreamEdit').length).toBe(1);
  });

  test('should show content error when user navigates to erroneous route', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/activity_stream/foo'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<ActivityStream />, {
        context: { router: { history } },
      });
    });
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
