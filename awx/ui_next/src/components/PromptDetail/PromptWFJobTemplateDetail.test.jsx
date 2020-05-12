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

  afterAll(() => {
    wrapper.unmount();
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
        .find('Detail[label="Options"]')
        .containsAllMatchingElements([
          <li>Enable Concurrent Jobs</li>,
          <li>Enable Webhooks</li>,
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
});
