import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import OrganizationDetail from '../../../../src/pages/Organizations/components/OrganizationDetail';

describe('<OrganizationDetail />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter initialEntries={['/organizations/1']} initialIndex={0}>
        <OrganizationDetail
          match={{ path: '/organizations/:id', url: '/organizations/1' }}
          location={{ search: '', pathname: '/organizations/1' }}
        />
      </MemoryRouter>
    );
  });
});
