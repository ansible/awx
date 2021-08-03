import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import Teams from './Teams';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
}));

describe('<Teams />', () => {
  test('initially renders successfully', () => {
    mountWithContexts(
      <Teams
        match={{ path: '/teams', url: '/teams' }}
        location={{ search: '', pathname: '/teams' }}
      />
    );
  });
});
