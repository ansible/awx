import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

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
              summary_fields: { related_field_counts: {
                users: 1,
                teams: 1,
              } }
            }}
            detailUrl="/organization/1"
            isSelected
            onSelect={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    );
  });
});
