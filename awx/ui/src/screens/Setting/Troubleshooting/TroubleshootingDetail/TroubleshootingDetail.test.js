import React from 'react';
import { act } from 'react-dom/test-utils';
import { SettingsProvider } from 'contexts/Settings';
import { SettingsAPI } from 'api';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import {
  assertDetail,
  assertVariableDetail,
} from '../../shared/settingTestUtils';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import mockJobSettings from '../../shared/data.jobSettings.json';
import JobsDetail from './JobsDetail';

jest.mock('../../../../api');

describe('<JobsDetail />', () => {
  let wrapper;

  beforeEach(() => {
    SettingsAPI.readCategory.mockResolvedValue({
      data: mockJobSettings,
    });
  });

  beforeEach(async () => {
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <JobsDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
  });

  afterAll(() => {
    jest.clearAllMocks();
  });

  test('initially renders without crashing', () => {
    expect(wrapper.find('JobsDetail').length).toBe(1);
  });

  test('should render expected tabs', () => {
    const expectedTabs = ['Back to Settings', 'Details'];
    wrapper.find('RoutedTabs li').forEach((tab, index) => {
      expect(tab.text()).toEqual(expectedTabs[index]);
    });
  });

  test('should render expected details', () => {
    assertDetail(wrapper, 'Job execution path', '/tmp');
    assertDetail(wrapper, 'Run Project Updates With Higher Verbosity', 'Off');
    assertDetail(wrapper, 'Enable Role Download', 'On');
    assertDetail(wrapper, 'Enable Collection(s) Download', 'On');
    assertDetail(wrapper, 'Follow symlinks', 'Off');
    assertDetail(
      wrapper,
      'Ignore Ansible Galaxy SSL Certificate Verification',
      'Off'
    );
    assertDetail(wrapper, 'Maximum Scheduled Jobs', '10');
    assertDetail(wrapper, 'Default Job Timeout', '0 seconds');
    assertDetail(wrapper, 'Default Job Idle Timeout', '0 seconds');
    assertDetail(wrapper, 'Default Inventory Update Timeout', '0 seconds');
    assertDetail(wrapper, 'Default Project Update Timeout', '0 seconds');
    assertDetail(wrapper, 'Per-Host Ansible Fact Cache Timeout', '0 seconds');
    assertDetail(wrapper, 'Maximum number of forks per job', '200');
    assertDetail(wrapper, 'Expose host paths for Container Groups', 'Off');
    assertVariableDetail(
      wrapper,
      'Ansible Modules Allowed for Ad Hoc Jobs',
      '[\n  "command"\n]'
    );
    assertVariableDetail(wrapper, 'Paths to expose to isolated jobs', '[]');
    assertVariableDetail(wrapper, 'Extra Environment Variables', '{}');
    assertVariableDetail(wrapper, 'Ansible Callback Plugins', '[]');
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
          <JobsDetail />
        </SettingsProvider>,
        {
          context: { config },
        }
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('Button[aria-label="Edit"]').exists()).toBeFalsy();
  });

  test('should display content error when api throws error on initial render', async () => {
    SettingsAPI.readCategory.mockRejectedValue(new Error());
    await act(async () => {
      wrapper = mountWithContexts(
        <SettingsProvider value={mockAllOptions.actions}>
          <JobsDetail />
        </SettingsProvider>
      );
    });
    await waitForElement(wrapper, 'ContentLoading', (el) => el.length === 0);
    expect(wrapper.find('ContentError').length).toBe(1);
  });
});
