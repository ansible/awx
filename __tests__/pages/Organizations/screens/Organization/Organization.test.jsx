import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import Organization from '../../../../../src/pages/Organizations/screens/Organization/Organization';

describe('<OrganizationView />', () => {
  const me = {
    is_super_user: true,
    is_system_auditor: false
  };
  test('initially renders succesfully', () => {
    mountWithContexts(<Organization me={me} />);
  });
});
