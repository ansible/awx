import React from 'react';
import { mountWithContexts } from '@testUtils/enzymeHelpers';
import Organizations from './Organizations';

jest.mock('@api');

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
