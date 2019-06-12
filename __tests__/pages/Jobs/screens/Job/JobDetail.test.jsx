import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import JobDetail from '../../../../../src/pages/Jobs/JobDetail/';

describe('<JobDetail />', () => {
  const mockDetails = {
    name: 'Foo'
  };

  test('initially renders succesfully', () => {
    mountWithContexts(
      <JobDetail job={ mockDetails } />
    );
  });
});
