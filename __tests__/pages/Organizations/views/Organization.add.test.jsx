import React from 'react';
import { mount } from 'enzyme';
import OrganizationAdd from '../../../../src/pages/Organizations/views/Organization.add';

describe('<OrganizationAdd />', () => {
  test('initially renders succesfully', () => {
    mount(
      <OrganizationAdd
        match={{ path: '/organizations/add', url: '/organizations/add' }}
        location={{ search: '', pathname: '/organizations/add' }}
      />
    );
  });
});
