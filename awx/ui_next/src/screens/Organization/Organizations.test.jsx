import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Organizations from './Organizations';

jest.mock('../../api');

describe('<Organizations />', () => {
  test('initially renders succesfully', async () => {
    await act(async () => {
      mountWithContexts(
        <Organizations
          match={{ path: '/organizations', url: '/organizations' }}
          location={{ search: '', pathname: '/organizations' }}
        />
      );
    });
  });
});
