import React from 'react';
import { mount } from 'enzyme';
import OrganizationListItem from '../../../../src/pages/Organizations/components/OrganizationListItem';

xdescribe('<OrganizationListItem />', () => {
  test('initially renders succesfully', () => {
    mount(
      <OrganizationListItem />
    );
  });
});
