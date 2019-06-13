import React from 'react';
import { mountWithContexts } from '../../../enzymeHelpers';
import TemplatesListItem from '../../../../src/pages/Templates/components/TemplateListItem';

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
