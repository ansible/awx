import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import OrganizationEdit from '../../../../../src/pages/Organizations/screens/Organization/OrganizationEdit';

describe('<OrganizationEdit />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter initialEntries={['/organizations/1/edit']} initialIndex={0}>
        <OrganizationEdit
          match={{ path: '/organizations/:id/edit', url: '/organizations/1/edit', params: { id: 1 } }}
        />
      </MemoryRouter>
    );
  });
});
