import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import JobOutput from '../../../../../src/pages/Jobs/JobOutput/';

describe('<JobOutput />', () => {
  const mockDetails = {
    name: 'Foo'
  };

  test('initially renders succesfully', () => {
    mountWithContexts(
      <JobOutput job={ mockDetails } />
    );
  });
});
