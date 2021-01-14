import React from 'react';
import { Link } from 'react-router-dom';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import StreamDetailButton from './StreamDetailButton';

jest.mock('../../api/models/ActivityStream');

describe('<StreamDetailButton />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <StreamDetailButton
        streamItem={{
          timestamp: '12:00:00',
        }}
        user={<Link to="/users/1/details">Bob</Link>}
        description={<span>foo</span>}
      />
    );
  });
});
