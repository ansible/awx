import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Job from './Jobs';

describe('<Job />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(<Job />);
  });
});
