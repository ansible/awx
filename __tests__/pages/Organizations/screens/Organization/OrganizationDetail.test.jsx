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
            match={{ url: '/organizations/1' }}
            organization={{ name: 'Default' }}
          />
        </MemoryRouter>
      </I18nProvider>
    );
  });
});
