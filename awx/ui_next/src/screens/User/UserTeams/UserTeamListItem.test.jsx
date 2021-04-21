import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
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
      <I18nProvider i18n={i18n}>
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
