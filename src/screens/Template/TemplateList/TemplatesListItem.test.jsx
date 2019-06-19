import React from 'react';

import { mountWithContexts } from '@testUtils/enzymeHelpers';

import TemplatesListItem from './TemplateListItem';

describe('<TemplatesListItem />', () => {
  test('initially render successfully', () => {
    mountWithContexts(<TemplatesListItem
      template={{
        id: 1,
        name: 'Template 1',
        url: '/templates/job_template/1',
        type: 'job_template'
      }}
    />);
  });
});
