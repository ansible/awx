import React from 'react';
import { mount } from 'enzyme';
import OrganizationDetail from '../../../../src/pages/Organizations/components/OrganizationDetail';

xdescribe('<OrganizationDetail />', () => {
  test('initially renders succesfully', () => {
    mount(
      <OrganizationDetail />
    );
  });
});
