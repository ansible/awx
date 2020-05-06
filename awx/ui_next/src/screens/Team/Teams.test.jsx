import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Teams from './Teams';

jest.mock('../../api');

describe('<Teams />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <Teams
        match={{ path: '/teams', url: '/teams' }}
        location={{ search: '', pathname: '/teams' }}
      />
    );
  });
});
