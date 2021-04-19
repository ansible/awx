import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { en } from 'make-plural/plurals';
import { i18n } from '@lingui/core';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import english from '../../../locales/en/messages';
import OrganizationListItem from './OrganizationListItem';

i18n.loadLocaleData({ en: { plurals: en } });
i18n.load({ en: english });
i18n.activate('en');

describe('<OrganizationListItem />', () => {
  test('initially renders successfully', () => {
    mountWithContexts(
      <I18nProvider i18n={i18n}>
        <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
          <table>
            <tbody>
              <OrganizationListItem
                organization={{
                  id: 1,
                  name: 'Org',
                  summary_fields: {
                    related_field_counts: {
                      users: 1,
                      teams: 1,
                    },
                    user_capabilities: {
                      edit: true,
                    },
                  },
                }}
                detailUrl="/organization/1"
                isSelected
                onSelect={() => {}}
              />
            </tbody>
          </table>
        </MemoryRouter>
      </I18nProvider>
    );
  });

  test('edit button shown to users with edit capabilities', () => {
    const wrapper = mountWithContexts(
      <I18nProvider i18n={i18n}>
        <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
          <table>
            <tbody>
              <OrganizationListItem
                organization={{
                  id: 1,
                  name: 'Org',
                  summary_fields: {
                    related_field_counts: {
                      users: 1,
                      teams: 1,
                    },
                    user_capabilities: {
                      edit: true,
                    },
                  },
                }}
                detailUrl="/organization/1"
                isSelected
                onSelect={() => {}}
              />
            </tbody>
          </table>
        </MemoryRouter>
      </I18nProvider>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });

  test('edit button hidden from users without edit capabilities', () => {
    const wrapper = mountWithContexts(
      <I18nProvider i18n={i18n}>
        <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
          <table>
            <tbody>
              <OrganizationListItem
                organization={{
                  id: 1,
                  name: 'Org',
                  summary_fields: {
                    related_field_counts: {
                      users: 1,
                      teams: 1,
                    },
                    user_capabilities: {
                      edit: false,
                    },
                  },
                }}
                detailUrl="/organization/1"
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

  test('should render warning about missing execution environment', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
          <OrganizationListItem
            organization={{
              id: 1,
              name: 'Org',
              summary_fields: {
                related_field_counts: {
                  users: 1,
                  teams: 1,
                },
                user_capabilities: {
                  edit: true,
                },
              },
              custom_virtualenv: '/var/lib/awx/env',
              default_environment: null,
            }}
            detailUrl="/organization/1"
            isSelected
            onSelect={() => {}}
          />
        </tbody>
      </table>
    );
    expect(
      wrapper.find('.missing-execution-environment').prop('content')
    ).toEqual(
      'Custom virtual environment /var/lib/awx/env must be replaced by an execution environment.'
    );
  });
});
