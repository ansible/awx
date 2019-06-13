import React from 'react';
import { mountWithContexts } from '../../enzymeHelpers';
import Templates from '../../../src/pages/Templates/Templates';

describe('<Templates />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <Templates />
    );
  });
});
