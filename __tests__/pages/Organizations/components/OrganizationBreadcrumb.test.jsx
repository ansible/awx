import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import OrganizationBreadcrumb from '../../../../src/pages/Organizations/components/OrganizationBreadcrumb';

describe('<OrganizationBreadcrumb />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
        <OrganizationBreadcrumb
          match={{ path: '/organizations', url: '/organizations' }}
          location={{ search: '', pathname: '/organizations' }}
          parentObj={[{ name: 'Organizations', url: '/organizations' }]}
        />
      </MemoryRouter>
    );
  });
});
