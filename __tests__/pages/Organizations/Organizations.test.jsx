import React from 'react';
import { mountWithContexts } from '../../enzymeHelpers';
import Organizations from '../../../src/pages/Organizations/Organizations';

describe('<Organizations />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <Organizations
        match={{ path: '/organizations', url: '/organizations' }}
        location={{ search: '', pathname: '/organizations' }}
      />
    );
  });
});
