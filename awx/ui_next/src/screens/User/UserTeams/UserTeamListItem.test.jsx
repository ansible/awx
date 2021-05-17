import React from 'react';
import { i18n } from '@lingui/core';
import { en } from 'make-plural/plurals';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';
import UserTeamListItem from './UserTeamListItem';
import english from '../../../locales/en/messages';

i18n.loadLocaleData({ en: { plurals: en } });
i18n.load({ en: english });
i18n.activate('en');

describe('<UserTeamListItem />', () => {
  test('should render item', () => {
    const wrapper = mountWithContexts(
      <table>
        <tbody>
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
        </tbody>
      </table>
    );

    const cells = wrapper.find('Td');
    expect(cells).toHaveLength(4);
    expect(cells.at(1).text()).toEqual('Team 1');
    expect(cells.at(2).text()).toEqual('The Org');
    expect(cells.at(3).text()).toEqual('something something team');
  });
});
