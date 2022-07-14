import React from 'react';
import { mountWithContexts } from '../../../testUtils/enzymeHelpers';
import PromptWFJobTemplateDetail from './PromptWFJobTemplateDetail';
import mockData from './data.workflow_template.json';

const mockWF = {
  ...mockData,
  webhook_key: 'Pim3mRXT0',
};

describe('PromptWFJobTemplateDetail', () => {
  let wrapper;

  beforeAll(() => {
    wrapper = mountWithContexts(
      <PromptWFJobTemplateDetail resource={mockWF} />
    );
  });

  test('should render successfully', () => {
    expect(wrapper.find('PromptWFJobTemplateDetail')).toHaveLength(1);
  });

  test('should render expected details', () => {
    function assertDetail(label, value) {
      expect(wrapper.find(`Detail[label="${label}"] dt`).text()).toBe(label);
      expect(wrapper.find(`Detail[label="${label}"] dd`).text()).toBe(value);
    }

    expect(wrapper.find('StatusIcon')).toHaveLength(1);
    assertDetail('Inventory', 'Mock Smart Inv');
    assertDetail('Source Control Branch', '/bar/');
    assertDetail('Limit', 'hosts1,hosts2');
    assertDetail('Webhook Service', 'Github');
    assertDetail('Webhook Key', 'Pim3mRXT0');
    expect(wrapper.find('Detail[label="Webhook URL"] dd').text()).toEqual(
      expect.stringContaining('/api/v2/workflow_job_templates/47/github/')
    );
    expect(
      wrapper
        .find('Detail[label="Enabled Options"]')
        .containsAllMatchingElements([
          <li>Concurrent Jobs</li>,
          <li>Webhooks</li>,
        ])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Webhook Credential"]')
        .containsAllMatchingElements([
          <span>
            <strong>Github Token:</strong>github
          </span>,
        ])
    ).toEqual(true);
    expect(
      wrapper
        .find('Detail[label="Labels"]')
        .containsAllMatchingElements([<span>L_10o0</span>, <span>L_20o0</span>])
    ).toEqual(true);
    expect(wrapper.find('VariablesDetail').prop('value')).toEqual(
      '---\nmock: data'
    );
  });

  test('should not load Activity', () => {
    wrapper = mountWithContexts(
      <PromptWFJobTemplateDetail
        resource={{
          ...mockWF,
          summary_fields: {
            recent_jobs: [],
          },
        }}
      />
    );
    const activity_detail = wrapper.find(`Detail[label="Activity"]`).at(0);
    expect(activity_detail.prop('isEmpty')).toEqual(true);
  });

  test('should not load Labels', () => {
    wrapper = mountWithContexts(
      <PromptWFJobTemplateDetail
        resource={{
          ...mockWF,
          summary_fields: {
            labels: {
              results: [],
            },
          },
        }}
      />
    );
    const labels_detail = wrapper.find(`Detail[label="Labels"]`).at(0);
    expect(labels_detail.prop('isEmpty')).toEqual(true);
  });
});
