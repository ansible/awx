import React from 'react';
import { mount } from 'enzyme';
import OrganizationView from '../../../../src/pages/Organizations/views/Organization.view';

xdescribe('<OrganizationView />', () => {
  test('initially renders succesfully', () => {
    mount(
      <OrganizationView />
    );
  });
});
