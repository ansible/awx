import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import mockDetails from '../data.user.json';
import UserListItem from './UserListItem';

let wrapper;

afterEach(() => {
  wrapper.unmount();
});

describe('UserListItem with full permissions', () => {
  beforeEach(() => {
    wrapper = mountWithContexts(
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
  test('initially renders succesfully', () => {
    expect(wrapper.length).toBe(1);
  });
  test('edit button shown to users with edit capabilities', () => {
    expect(wrapper.find('PencilAltIcon').exists()).toBeTruthy();
  });
});

describe('UserListItem without full permissions', () => {
  test('edit button hidden from users without edit capabilities', () => {
    wrapper = mountWithContexts(
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
