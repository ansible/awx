import React from 'react';
import { act } from 'react-dom/test-utils';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import { SettingsProvider } from '../../../../contexts/Settings';
import { SettingsAPI } from '../../../../api';
import { assertDetail } from '../../shared/settingTestUtils';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import TACACSDetail from './TACACSDetail';

jest.mock('../../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({
  data: {
    TACACSPLUS_HOST: 'mockhost',
    TACACSPLUS_PORT: 49,
    TACACSPLUS_SECRET: '$encrypted$',
    TACACSPLUS_SESSION_TIMEOUT: 5,
    TACACSPLUS_AUTH_PROTOCOL: 'ascii',
  },
});

describe('<TACACSDetail />', () => {
  let wrapper;

  beforeAll(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <TACACSDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
  });

  afterAll(() => {
    wrapper.unmount();
    jest.clearAllMocks();
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('TACACSDetail').length).toBe(1);
  });

  test('should render expected tabs', () => {
    const expectedTabs = ['Back to Settings', 'Details'];
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should render expected details', () => {
    assertDetail(wrapper, 'TACACS+ Server', 'mockhost');
    assertDetail(wrapper, 'TACACS+ Port', '49');
    assertDetail(wrapper, 'TACACS+ Secret', 'Encrypted');
    assertDetail(wrapper, 'TACACS+ Auth Session Timeout', '5 seconds');
    assertDetail(wrapper, 'TACACS+ Authentication Protocol', 'ascii');
  });

  test('should hide edit button from non-superusers', async () => {
    const config = {
      me: {
        is_superuser: false,
      },
    };
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <TACACSDetail />
        </SettingsProvider>,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('Button[aria-label="Edit"]').exists()).toBeFalsy();
  });

  test('should display content error when api throws error on initial render', async () => {
    SettingsAPI.readCategory.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <TACACSDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
