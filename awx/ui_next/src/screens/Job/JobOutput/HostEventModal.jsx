import React, { useEffect, useState } from 'react';
import { Modal as PFModal, Tab, Tabs as PFTabs } from '@patternfly/react-core';
import CodeMirrorInput from '@components/CodeMirrorInput';
import ContentEmpty from '@components/ContentEmpty';
import PropTypes from 'prop-types';
import { DetailList, Detail } from '@components/DetailList';
import StatusIcon from '@components/StatusIcon';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import Entities from 'html-entities';

const entities = new Entities.AllHtmlEntities();

const Modal = styled(PFModal)`
  --pf-c-modal-box__footer--MarginTop: 0;
  align-self: flex-start;
  margin-top: 200px;
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
  grid-template-columns: auto auto;
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

const processEventStatus = event => {
  let status = null;
  if (event.event === 'runner_on_unreachable') {
    status = 'unreachable';
  }
  // equiv to 'runner_on_error' && 'runner_on_failed'
  if (event.failed) {
    status = 'failed';
  }
  if (
    event.event === 'runner_on_ok' ||
    event.event === 'runner_on_async_ok' ||
    event.event === 'runner_item_on_ok'
  ) {
    status = 'ok';
  }
  // if 'ok' and 'changed' are both true, show 'changed'
  if (event.changed) {
    status = 'changed';
  }
  if (event.event === 'runner_on_skipped') {
    status = 'skipped';
  }
  return status;
};

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

const processStdOutValue = hostEvent => {
  const taskAction = hostEvent?.event_data?.taskAction;
  const res = hostEvent?.event_data?.res;

  let stdOut;
  if (taskAction === 'debug' && res.result && res.result.stdout) {
    stdOut = res.result.stdout;
  } else if (
    taskAction === 'yum' &&
    res.results &&
    Array.isArray(res.results)
  ) {
    [stdOut] = res.results;
  } else if (res) {
    stdOut = res.stdout;
  }
  return stdOut;
};

function HostEventModal({ onClose, hostEvent = {}, isOpen = false, i18n }) {
  const [hostStatus, setHostStatus] = useState(null);
  const [activeTabKey, setActiveTabKey] = useState(0);

  useEffect(() => {
    setHostStatus(processEventStatus(hostEvent));
  }, [setHostStatus, hostEvent]);

  const handleTabClick = (event, tabIndex) => {
    setActiveTabKey(tabIndex);
  };

  const jsonObj = processCodeMirrorValue(hostEvent?.event_data?.res);
  const stdErr = processCodeMirrorValue(hostEvent?.event_data?.res?.stderr);
  const stdOut = processCodeMirrorValue(processStdOutValue(hostEvent));

  return (
    <Modal
      isFooterLeftAligned
      isLarge
      isOpen={isOpen}
      onClose={onClose}
      title={i18n._(t`Host Details`)}
    >
      <Tabs
        aria-label={i18n._(t`Tabs`)}
        activeKey={activeTabKey}
        onSelect={handleTabClick}
      >
        <Tab
          aria-label={i18n._(t`Details tab`)}
          eventKey={0}
          title={i18n._(t`Details`)}
        >
          <DetailList style={{ alignItems: 'center' }} gutter="sm">
            <Detail
              label={i18n._(t`Host Name`)}
              value={
                <HostNameDetailValue>
                  {hostStatus ? <StatusIcon status={hostStatus} /> : null}
                  {hostEvent.host_name}
                </HostNameDetailValue>
              }
            />
            <Detail label={i18n._(t`Play`)} value={hostEvent.play} />
            <Detail label={i18n._(t`Task`)} value={hostEvent.task} />
            <Detail
              label={i18n._(t`Module`)}
              value={
                hostEvent.event_data.task_action || i18n._(t`No result found`)
              }
            />
            <Detail
              label={i18n._(t`Command`)}
              value={hostEvent?.event_data?.res?.cmd}
            />
          </DetailList>
        </Tab>
        <Tab
          eventKey={1}
          title={i18n._(t`JSON`)}
          aria-label={i18n._(t`JSON tab`)}
        >
          {activeTabKey === 1 && jsonObj ? (
            <CodeMirrorInput
              mode="javascript"
              readOnly
              value={JSON.stringify(jsonObj, null, 2)}
              onChange={() => {}}
              rows={20}
              hasErrors={false}
            />
          ) : (
            <ContentEmpty title={i18n._(t`No JSON Available`)} />
          )}
        </Tab>
        <Tab
          eventKey={2}
          title={i18n._(t`Standard Out`)}
          aria-label={i18n._(t`Standard out tab`)}
        >
          {activeTabKey === 2 && stdOut ? (
            <CodeMirrorInput
              mode="javascript"
              readOnly
              value={stdOut}
              onChange={() => {}}
              rows={20}
              hasErrors={false}
            />
          ) : (
            <ContentEmpty title={i18n._(t`No Standard Out Available`)} />
          )}
        </Tab>
        <Tab
          eventKey={3}
          title={i18n._(t`Standard Error`)}
          aria-label={i18n._(t`Standard error tab`)}
        >
          {activeTabKey === 3 && stdErr ? (
            <CodeMirrorInput
              mode="javascript"
              readOnly
              onChange={() => {}}
              value={stdErr}
              hasErrors={false}
              rows={20}
            />
          ) : (
            <ContentEmpty title={i18n._(t`No Standard Error Available`)} />
          )}
        </Tab>
      </Tabs>
    </Modal>
  );
}

export default withI18n()(HostEventModal);

HostEventModal.propTypes = {
  onClose: PropTypes.func.isRequired,
  hostEvent: PropTypes.shape({}),
  isOpen: PropTypes.bool,
};

HostEventModal.defaultProps = {
  hostEvent: null,
  isOpen: false,
};
