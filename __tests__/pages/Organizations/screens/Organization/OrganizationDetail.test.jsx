import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import { I18nProvider } from '@lingui/react';
import OrganizationDetail from '../../../../../src/pages/Organizations/screens/Organization/OrganizationDetail';

describe('<OrganizationDetail />', () => {
  test('initially renders succesfully', () => {
    mount(
      <I18nProvider>
        <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
          <OrganizationDetail
            match={{ path: '/organizations/:id', url: '/organizations/1' }}
            location={{ search: '', pathname: '/organizations/1' }}
            params={{}}
          />
        </MemoryRouter>
      </I18nProvider>
    );
  });
});
