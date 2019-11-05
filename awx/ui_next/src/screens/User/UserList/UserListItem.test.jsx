import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import mockDetails from '../data.user.json';
import UserListItem from './UserListItem';

describe('<UserListItem />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <I18nProvider>
        <MemoryRouter initialEntries={['/users']} initialIndex={0}>
          <UserListItem
            user={mockDetails}
            detailUrl="/user/1"
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
        <MemoryRouter initialEntries={['/users']} initialIndex={0}>
          <UserListItem
            user={mockDetails}
            detailUrl="/user/1"
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
        <MemoryRouter initialEntries={['/users']} initialIndex={0}>
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
        </MemoryRouter>
      </I18nProvider>
    );
    expect(wrapper.find('PencilAltIcon').exists()).toBeFalsy();
  });
});
