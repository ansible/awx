import React from 'react';
import { act } from 'react-dom/test-utils';
import { useRouteMatch } from 'react-router-dom';
import {
  mountWithContexts,
  waitForElement,
} from '../../../../../testUtils/enzymeHelpers';
import { SettingsProvider } from '../../../../contexts/Settings';
import { SettingsAPI } from '../../../../api';
import {
  assertDetail,
  assertVariableDetail,
} from '../../shared/settingTestUtils';
import mockAllOptions from '../../shared/data.allSettingOptions.json';
import mockLDAP from '../../shared/data.ldapSettings.json';
import LDAPDetail from './LDAPDetail';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useRouteMatch: jest.fn(),
}));
jest.mock('../../../../api/models/Settings');
SettingsAPI.readCategory.mockResolvedValue({ data: mockLDAP });

describe('<LDAPDetail />', () => {
  describe('Default', () => {
    let wrapper;

    beforeAll(async () => {
      useRouteMatch.mockImplementation(() => ({
        url: '/settings/ldap/default/details',
        path: '/settings/ldap/:category/details',
        params: { category: 'default' },
      }));
      await act(async () => {
        wrapper = mountWithContexts(
          <SettingsProvider value={mockAllOptions.actions}>
            <LDAPDetail />
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
      expect(wrapper.find('LDAPDetail').length).toBe(1);
    });

    test('should render expected tabs', () => {
      const expectedTabs = [
        'Back to Settings',
        'Default',
        'LDAP1',
        'LDAP2',
        'LDAP3',
        'LDAP4',
        'LDAP5',
      ];
      wrapper.find('RoutedTabs li').forEach((tab, index) => {
        expect(tab.text()).toEqual(expectedTabs[index]);
      });
    });

    test('should render expected details', () => {
      assertDetail(wrapper, 'LDAP Server URI', 'ldap://ldap.example.com');
      assertDetail(wrapper, 'LDAP Bind DN', 'cn=eng_user');
      assertDetail(wrapper, 'LDAP Bind Password', 'Encrypted');
      assertDetail(wrapper, 'LDAP Start TLS', 'Off');
      assertDetail(
        wrapper,
        'LDAP User DN Template',
        'uid=%(user)s,OU=Users,DC=example,DC=com'
      );
      assertDetail(wrapper, 'LDAP Group Type', 'MemberDNGroupType');
      assertDetail(
        wrapper,
        'LDAP Require Group',
        'CN=Tower Users,OU=Users,DC=example,DC=com'
      );
      assertDetail(wrapper, 'LDAP Deny Group', 'Not configured');
      assertVariableDetail(wrapper, 'LDAP User Search', '[]');
      assertVariableDetail(wrapper, 'LDAP User Attribute Map', '{}');
      assertVariableDetail(wrapper, 'LDAP Group Search', '[]');
      assertVariableDetail(
        wrapper,
        'LDAP Group Type Parameters',
        '{\n  "name_attr": "cn",\n  "member_attr": "member"\n}'
      );
      assertVariableDetail(wrapper, 'LDAP User Flags By Group', '{}');
      assertVariableDetail(wrapper, 'LDAP Organization Map', '{}');
      assertVariableDetail(wrapper, 'LDAP Team Map', '{}');
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
            <LDAPDetail />
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
            <LDAPDetail />
          </SettingsProvider>
        );
      });
      await waitForElement(wrapper, 'ContentLoading', el => el.length === 0);
      expect(wrapper.find('ContentError').length).toBe(1);
    });
  });

  describe('Redirect', () => {
    test('should render redirect when user navigates to erroneous category', async () => {
      let wrapper;
      useRouteMatch.mockImplementation(() => ({
        url: '/settings/ldap/foo/details',
        path: '/settings/ldap/:category/details',
        params: { category: 'foo' },
      }));
      await act(async () => {
        wrapper = mountWithContexts(
          <SettingsProvider value={mockAllOptions.actions}>
            <LDAPDetail />
          </SettingsProvider>
        );
      });
      await waitForElement(wrapper, 'Redirect');
    });
  });
});
