import React from 'react';
import { mount } from 'enzyme';
import OrganizationBreadcrumb from '../../../../src/pages/Organizations/components/OrganizationBreadcrumb';

xdescribe('<OrganizationBreadcrumb />', () => {
  test('initially renders succesfully', () => {
    mount(
      <OrganizationBreadcrumb />
    );
  });
});
