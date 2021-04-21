import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';

import { i18n } from '@lingui/core';
import { en } from 'make-plural/plurals';
import { mountWithContexts } from '../../../../testUtils/enzymeHelpers';

import TeamListItem from './TeamListItem';
import english from '../../../locales/en/messages';

i18n.loadLocaleData({ en: { plurals: en } });
i18n.load({ en: english });
i18n.activate('en');

describe('<TeamListItem />', () => {
  test('initially renders successfully', () => {
    mountWithContexts(
      <I18nProvider i18n={i18n}>
        <MemoryRouter initialEntries={['/teams']} initialIndex={0}>
          <table>
            <tbody>
              <TeamListItem
                team={{
                  id: 1,
                  name: 'Team 1',
                  summary_fields: {
                    user_capabilities: {
                      edit: true,
                    },
                  },
                }}
                detailUrl="/team/1"
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
        <MemoryRouter initialEntries={['/teams']} initialIndex={0}>
          <table>
            <tbody>
              <TeamListItem
                team={{
                  id: 1,
                  name: 'Team',
                  summary_fields: {
                    user_capabilities: {
                      edit: true,
                    },
                  },
                }}
                detailUrl="/team/1"
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
        <MemoryRouter initialEntries={['/teams']} initialIndex={0}>
          <table>
            <tbody>
              <TeamListItem
                team={{
                  id: 1,
                  name: 'Team',
                  summary_fields: {
                    user_capabilities: {
                      edit: false,
                    },
                  },
                }}
                detailUrl="/team/1"
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
