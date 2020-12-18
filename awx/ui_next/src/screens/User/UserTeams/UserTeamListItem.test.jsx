import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import UserTeamListItem from './UserTeamListItem';

describe('<UserTeamListItem />', () => {
  test('should render item', () => {
    const wrapper = mountWithContexts(
      <I18nProvider>
        <MemoryRouter initialEntries={['/teams']} initialIndex={0}>
          <UserTeamListItem
            team={{
              id: 1,
              name: 'Team 1',
              description: 'something something team',
              summary_fields: {
                organization: {
                  id: 2,
                  name: 'The Org',
                },
              },
            }}
            detailUrl="/team/1"
            isSelected={false}
            onSelect={() => {}}
          />
        </MemoryRouter>
      </I18nProvider>
    );

    const cells = wrapper.find('DataListCell');
    expect(cells).toHaveLength(3);
    expect(cells.at(0).text()).toEqual('Team 1');
    expect(cells.at(1).text()).toEqual('Organization The Org');
    expect(cells.at(2).text()).toEqual('something something team');
  });
});
