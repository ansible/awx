import React from 'react';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Job from './Jobs';

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<Job />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(<Job />);
  });
});
