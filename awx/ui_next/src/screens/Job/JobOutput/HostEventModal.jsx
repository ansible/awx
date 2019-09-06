import React, { useEffect, useState } from 'react';
import {
  Button,
  Modal as PFModal,
  Tab,
  Tabs as PFTabs,
} from '@patternfly/react-core';
import CodeMirrorInput from '@components/CodeMirrorInput';
import ContentEmpty from '@components/ContentEmpty';
import { DetailList, Detail } from '@components/DetailList';
import { HostStatusIcon } from '@components/Sparkline';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import Entities from 'html-entities';

const entities = new Entities.AllHtmlEntities();

const Modal = styled(PFModal)`
  --pf-c-modal-box__footer--MarginTop: 0;
  .pf-c-modal-box__body {
    overflow-y: hidden;
  }
  .pf-c-tab-content {
    padding: 24px 0;
  }
`;

const HostNameDetailValue = styled.div`
  align-items: center;
  display: inline-grid;
  grid-gap: 10px;
  grid-template-columns: min-content auto;
`;

const Tabs = styled(PFTabs)`
  --pf-c-tabs__button--PaddingLeft: 20px;
  --pf-c-tabs__button--PaddingRight: 20px;

  .pf-c-tabs__list {
    li:first-of-type .pf-c-tabs__button {
      &::after {
        margin-left: 0;
      }
    }
  }

  &:not(.pf-c-tabs__item)::before {
    position: absolute;
    top: 0;
    right: 0;
    bottom: 0;
    left: 0;
    content: '';
    border-bottom: solid var(--pf-c-tabs__item--BorderColor);
    border-width: var(--pf-c-tabs__item--BorderWidth) 0
      var(--pf-c-tabs__item--BorderWidth) 0;
  }
`;

function HostEventModal({ handleClose, hostEvent, isOpen, i18n }) {
  const [hostStatus, setHostStatus] = useState(null);
  const [activeTabKey, setActiveTabKey] = useState(0);

  useEffect(() => {
    processEventStatus(hostEvent);
  }, []);

  const handleTabClick = (event, tabIndex) => {
    setActiveTabKey(tabIndex);
  };

  function processEventStatus(event) {
    let status = null;
    if (event.event === 'runner_on_unreachable') {
      status = 'unreachable';
    }
    // equiv to 'runner_on_error' && 'runner_on_failed'
    if (event.failed) {
      status = 'failed';
    }
    // catch the 'changed' case before 'ok', because both can be true
    if (event.changed) {
      status = 'changed';
    }
    if (
      event.event === 'runner_on_ok' ||
      event.event === 'runner_on_async_ok' ||
      event.event === 'runner_item_on_ok'
    ) {
      status = 'ok';
    }
    if (event.event === 'runner_on_skipped') {
      status = 'skipped';
    }
    setHostStatus(status);
  }

  function processStdOutValue() {
    const { res } = hostEvent.event_data;
    let stdOut;
    if (taskAction === 'debug' && res.result && res.result.stdout) {
      stdOut = processCodeMirrorValue(res.result.stdout);
    } else if (
      taskAction === 'yum' &&
      res.results &&
      Array.isArray(res.results)
    ) {
      stdOut = processCodeMirrorValue(res.results[0]);
    } else {
      stdOut = processCodeMirrorValue(res.stdout);
    }
    return stdOut;
  }

  const processCodeMirrorValue = value => {
    let codeMirrorValue;
    if (value === undefined) {
      codeMirrorValue = false;
    } else if (value === '') {
      codeMirrorValue = ' ';
    } else if (typeof value === 'string') {
      codeMirrorValue = entities.encode(value);
    } else {
      codeMirrorValue = value;
    }
    return codeMirrorValue;
  };

  const taskAction = hostEvent.event_data.task_action;
  const JSONObj = processCodeMirrorValue(hostEvent.event_data.res);
  const StdErr = processCodeMirrorValue(hostEvent.event_data.res.stderr);
  const StdOut = processStdOutValue();

  return (
    <Modal
      isLarge
      isOpen={isOpen}
      onClose={handleClose}
      title={i18n._(t`Host Details`)}
      actions={[
        <Button key="cancel" variant="secondary" onClick={handleClose}>
          {i18n._(t`Close`)}
        </Button>,
      ]}
    >
      <Tabs activeKey={activeTabKey} onSelect={handleTabClick}>
        <Tab eventKey={0} title={i18n._(t`Details`)}>
          <DetailList style={{ alignItems: 'center' }} gutter="sm">
            <Detail
              label={i18n._(t`Host Name`)}
              value={
                <HostNameDetailValue>
                  {hostStatus && <HostStatusIcon status={hostStatus} />}
                  {hostEvent.host_name}
                </HostNameDetailValue>
              }
            />
            <Detail label={i18n._(t`Play`)} value={hostEvent.play} />
            <Detail label={i18n._(t`Task`)} value={hostEvent.task} />
            <Detail
              label={i18n._(t`Module`)}
              value={taskAction || i18n._(t`No result found`)}
            />
            <Detail
              label={i18n._(t`Command`)}
              value={hostEvent.event_data.res.cmd}
            />
          </DetailList>
        </Tab>
        <Tab eventKey={1} title={i18n._(t`JSON`)}>
          {activeTabKey === 1 && JSONObj ? (
            <CodeMirrorInput
              mode="javascript"
              readOnly
              value={JSON.stringify(JSONObj, null, 2)}
              onChange={() => {}}
              rows={20}
              hasErrors={false}
            />
          ) : (
            <ContentEmpty title={i18n._(t`No JSON Found`)} />
          )}
        </Tab>
        <Tab eventKey={2} title={i18n._(t`Standard Out`)}>
          {activeTabKey === 2 && StdOut ? (
            <CodeMirrorInput
              mode="javascript"
              readOnly
              value={StdOut}
              onChange={() => {}}
              rows={20}
              hasErrors={false}
            />
          ) : (
            <ContentEmpty title={i18n._(t`No Standard Out Found`)} />
          )}
        </Tab>
        <Tab eventKey={3} title={i18n._(t`Standard Error`)}>
          {activeTabKey === 3 && StdErr ? (
            <CodeMirrorInput
              mode="javascript"
              readOnly
              onChange={() => {}}
              value={StdErr}
              hasErrors={false}
              rows={20}
            />
          ) : (
            <ContentEmpty title={i18n._(t`No Standard Error Found`)} />
          )}
        </Tab>
      </Tabs>
    </Modal>
  );
}

export default withI18n()(HostEventModal);
