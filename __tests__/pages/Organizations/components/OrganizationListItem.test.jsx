import React from 'react';
import { mount } from 'enzyme';
import { MemoryRouter } from 'react-router-dom';
import OrganizationListItem from '../../../../src/pages/Organizations/components/OrganizationListItem';

describe('<OrganizationListItem />', () => {
  test('initially renders succesfully', () => {
    mount(
      <MemoryRouter initialEntries={['/organizations']} initialIndex={0}>
        <OrganizationListItem />
      </MemoryRouter>
    );
  });
});
