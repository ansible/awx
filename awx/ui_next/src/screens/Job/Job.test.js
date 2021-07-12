import React from 'react';
import { act } from 'react-dom/test-utils';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';

import Job from './Job';

jest.mock('../../api');
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useParams: () => ({
    id: 1,
    typeSegment: 'project',
  }),
}));

describe('<Job />', () => {
  test('initially renders successfully', async () => {
    await act(async () => {
      await mountWithContexts(<Job setBreadcrumb={() => {}} />);
    });
  });
});
