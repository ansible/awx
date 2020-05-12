import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import OrganizationListItem from './OrganizationListItem';

describe('<OrganizationListItem />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
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
        </MemoryRouter>
      </I18nProvider>
    );
  });
  test('edit button shown to users with edit capabilities', () => {
    const wrapper = mountWithContexts(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
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
        </MemoryRouter>
      </I18nProvider>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });
  test('edit button hidden from users without edit capabilities', () => {
    const wrapper = mountWithContexts(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
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
        </MemoryRouter>
      </I18nProvider>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});
