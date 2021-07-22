import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import { SettingsAPI, RootAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import mockAllSettings from '../shared/data.allSettings.json';
import Subscription from './Subscription';

jest.mock('../../../api');
SettingsAPI.readCategory.mockResolvedValue({
  data: mockAllSettings,
});
RootAPI.readAssetVariables.mockResolvedValue({
  data: {
    BRAND_NAME: 'AWX',
    PENDO_API_KEY: '',
  },
});

describe('<Subscription />', () => {
  let wrapper;

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('should redirect to subscription details', async () => {
    const history = createMemoryHistory({
      initialEntries: ['/settings/subscription'],
    });
    await act(async () => {
      wrapper = mountWithContexts(<Subscription />, {
        context: {
          router: {
            history,
          },
          config: {
            license_info: {
              license_type: 'enterprise',
              automated_instances: '1',
              automated_since: '1614714228',
            },
          },
        },
      });
    });
    await waitForElement(
      wrapper,
      'SubscriptionDetail',
      (el) => el.length === 1
    );
  });
});
