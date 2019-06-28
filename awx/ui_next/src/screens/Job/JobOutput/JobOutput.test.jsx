import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import JobOutput from './JobOutput';

describe('<JobOutput />', () => {
  const mockDetails = {
    name: 'Foo',
  };

  test('initially renders succesfully', () => {
    mountWithContexts(<JobOutput job={mockDetails} />);
  });
});
