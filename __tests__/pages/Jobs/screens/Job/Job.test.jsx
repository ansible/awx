import React from 'react';
import { mountWithContexts } from '../../../../enzymeHelpers';
import Job from '../../../../../src/pages/Jobs/Job';


describe('<Job />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(<Job />);
  });
});
