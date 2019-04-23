import React from 'react';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import { mountWithContexts } from '../../../enzymeHelpers';
import OrganizationListItem from '../../../../src/pages/Organizations/components/OrganizationListItem';

describe('<OrganizationListItem />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
          <OrganizationListItem />
        </MemoryRouter>
      </I18nProvider>
    );
  });
});
