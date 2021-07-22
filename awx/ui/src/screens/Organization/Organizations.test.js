import React from 'react';
import { act } from 'react-dom/test-utils';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Organizations from './Organizations';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<Organizations />', () => {
  test('initially renders successfully', async () => {
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
