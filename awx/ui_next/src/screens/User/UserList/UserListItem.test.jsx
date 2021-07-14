import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { i18n } from '@lingui/core';
import { en } from 'make-plural/plurals';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import mockDetails from '../data.user.json';
import UserListItem from './UserListItem';
import english from '../../../locales/en/messages';

i18n.loadLocaleData({ en: { plurals: en } });
i18n.load({ en: english });
i18n.activate('en');

let wrapper;

describe('UserListItem with full permissions', () => {
  beforeEach(() => {
    wrapper = mountWithContexts(
      <I18nProvider i18n={i18n}>
        <MemoryRouter initialEntries={['/users']} initialIndex={0}>
          <table>
            <tbody>
              <UserListItem
                user={mockDetails}
                detailUrl="/user/1"
                isSelected
                onSelect={() => {}}
              />
            </tbody>
          </table>
        </MemoryRouter>
      </I18nProvider>
    );
  });

  test('initially renders successfully', () => {
    expect(wrapper.length).toBe(1);
  });

  test('edit button shown to users with edit capabilities', () => {
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('should display user data', () => {
    expect(wrapper.find('td[data-label="Role"]').prop('children')).toEqual(
      'System Administrator'
    );
    expect(
      wrapper.find('Label[aria-label="social login"]').prop('children')
    ).toEqual('SOCIAL');
  });
});

describe('UserListItem without full permissions', () => {
  test('edit button hidden from users without edit capabilities', () => {
    wrapper = mountWithContexts(
      <I18nProvider i18n={i18n}>
        <MemoryRouter initialEntries={['/users']} initialIndex={0}>
          <table>
            <tbody>
              <UserListItem
                user={{
                  ...mockDetails,
                  summary_fields: {
                    user_capabilities: {
                      edit: false,
                    },
                  },
                }}
                detailUrl="/user/1"
                isSelected
                onSelect={() => {}}
              />
            </tbody>
          </table>
        </MemoryRouter>
      </I18nProvider>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});
