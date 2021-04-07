import React from 'react';
import { act } from 'react-dom/test-utils';
import { createMemoryHistory } from 'history';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../testUtils/enzymeHelpers';
import mockAllSettings from '../shared/data.allSettings.json';
import { SettingsAPI, RootAPI } from '../../../api';
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
    wrapper.unmount();
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
            },
          },
        },
      });
    });
    await waitForElement(wrapper, 'SubscriptionDetail', el => el.length === 1);
  });
});
