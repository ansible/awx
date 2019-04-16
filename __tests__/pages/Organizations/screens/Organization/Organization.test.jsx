import React from 'react';
import { mount } from 'enzyme';

import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import Organization from '../../../../../src/pages/Organizations/screens/Organization/Organization';

describe('<OrganizationView />', () => {
  test('initially renders succesfully', () => {
    mount(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
          <Organization
            match={{ path: '/organizations/:id', url: '/organizations/1' }}
            location={{ search: '', pathname: '/organizations/1' }}
          />
        </MemoryRouter>
      </I18nProvider>
    );
  });
});
