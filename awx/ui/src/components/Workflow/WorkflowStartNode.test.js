import React from 'react';

import { en } from 'make-plural/plurals';
import { I18nProvider } from '@lingui/react';
import { i18n } from '@lingui/core';
import { WorkflowStateContext } from 'contexts/Workflow';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import english from '../../locales/en/messages';
import WorkflowStartNode from './WorkflowStartNode';

const nodePositions = {
  1: {
    x: 0,
    y: 0,
  },
};

i18n.loadLocaleData({ en: { plurals: en } });
i18n.load({ en: english });
i18n.activate('en');

describe('WorkflowStartNode', () => {
  test('mounts successfully', () => {
    const wrapper = mountWithContexts(
      <svg>
        <I18nProvider i18n={i18n}>
          <WorkflowStateContext.Provider value={{ nodePositions }}>
            <WorkflowStartNode
              nodePositions={nodePositions}
              showActionTooltip={false}
            />
          </WorkflowStateContext.Provider>
        </I18nProvider>
      </svg>
    );
    expect(wrapper).toHaveLength(1);
  });
  test('tooltip shown on hover', () => {
    const wrapper = mountWithContexts(
      <svg>
        <I18nProvider i18n={i18n}>
          <WorkflowStateContext.Provider value={{ nodePositions }}>
            <WorkflowStartNode
              nodePositions={nodePositions}
              showActionTooltip
            />
          </WorkflowStateContext.Provider>
        </I18nProvider>
      </svg>
    );
    expect(wrapper.find('WorkflowActionTooltip')).toHaveLength(0);
    wrapper.find('WorkflowStartNode').simulate('mouseenter');
    expect(wrapper.find('WorkflowActionTooltip')).toHaveLength(1);
    wrapper.find('WorkflowStartNode').simulate('mouseleave');
    expect(wrapper.find('WorkflowActionTooltip')).toHaveLength(0);
  });
});
