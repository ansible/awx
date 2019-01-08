import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import OrganizationsList from '../../../../src/pages/Organizations/screens/OrganizationsList';

describe('<OrganizationsList />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
        <I18nProvider>
          <OrganizationsList
            match={{ path: '/organizations', url: '/organizations' }}
            location={{ search: '', pathname: '/organizations' }}
          />
        </I18nProvider>
      </MemoryRouter>
    );
  });
});
