import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import TeamListItem from './TeamListItem';

describe('<TeamListItem />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <I18nProvider>
        <MemoryRouter initialEntries={['/teams']} initialIndex={0}>
          <TeamListItem
            team={{
              id: 1,
              name: 'Team 1',
              summary_fields: {
                organization: {
                  id: 1,
                  name: 'Default',
                },
              },
            }}
            detailUrl="/team/1"
            isSelected
            onSelect={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    );
  });
});
