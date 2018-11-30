import React from 'react';
import { mount } from 'enzyme';
import OrganizationAdd from '../../../../src/pages/Organizations/views/Organization.add';

xdescribe('<OrganizationAdd />', () => {
  test('initially renders succesfully', () => {
    mount(
      <OrganizationAdd />
    );
  });
});
