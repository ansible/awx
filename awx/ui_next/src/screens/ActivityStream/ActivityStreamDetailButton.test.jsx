import React from 'react';
import { Link } from 'react-router-dom';

import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import ActivityStreamDetailButton from './ActivityStreamDetailButton';

jest.mock('../../api/models/ActivityStream');

describe('<ActivityStreamDetailButton />', () => {
  test('initially renders succesfully', () => {
    mountWithContexts(
      <ActivityStreamDetailButton
        streamItem={{
          timestamp: '12:00:00',
        }}
        user={<Link to="/users/1/details">Bob</Link>}
        description={<span>foo</span>}
      />
    );
  });
});
