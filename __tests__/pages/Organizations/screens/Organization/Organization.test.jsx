import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import Organization from '../../../../../src/pages/Organizations/screens/Organization/Organization';

describe('<OrganizationView />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(<Organization />);
  });
});
