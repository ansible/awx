import React from 'react';
import { mount } from 'enzyme';
import OrganizationEdit from '../../../../src/pages/Organizations/components/OrganizationEdit';

xdescribe('<OrganizationEdit />', () => {
  test('initially renders succesfully', () => {
    mount(
      <OrganizationEdit />
    );
  });
});
