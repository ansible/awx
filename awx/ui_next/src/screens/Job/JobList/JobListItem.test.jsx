import React from 'react';
import { createMemoryHistory } from 'history';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import JobListItem from './JobListItem';

describe('<JobListItem />', () => {
  test('initially renders succesfully', () => {
    const history = createMemoryHistory({
      initialEntries: ['/jobs'],
    });
    mountWithContexts(
      <JobListItem
        job={{
          id: 1,
          name: 'Job',
          type: 'project update',
          summary_fields: {
            user_capabilities: {
              start: true,
            },
          },
        }}
        detailUrl="/organization/1"
        isSelected
        onSelect={() => {}}
      />,
      { context: { router: { history } } }
    );
  });
});
