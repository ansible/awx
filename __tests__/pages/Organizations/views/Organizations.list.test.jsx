import React from 'react';
import { mount } from 'enzyme';
import OrganizationsList from '../../../../src/pages/Organizations/views/Organizations.list';

xdescribe('<OrganizationsList />', () => {
  test('initially renders succesfully', () => {
    mount(
      <OrganizationsList />
    );
  });
});
