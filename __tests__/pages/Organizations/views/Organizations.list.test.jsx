import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import OrganizationsList from '../../../../src/pages/Organizations/views/Organizations.list';

describe('<OrganizationsList />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
        <OrganizationsList
          match={{ path: '/organizations', url: '/organizations' }}
          location={{ search: '', pathname: '/organizations' }}
        />
      </MemoryRouter>
    );
  });
});
