import React, { useEffect, useState } from 'react';
import { Modal, Tab, Tabs, TabTitleText } from '@patternfly/react-core';
import PropTypes from 'prop-types';
import { withI18n } from '@lingui/react';
import { t } from '@lingui/macro';
import styled from 'styled-components';
import { AllHtmlEntities } from 'html-entities';
import StatusIcon from '../../../components/StatusIcon';
import { DetailList, Detail } from '../../../components/DetailList';
import ContentEmpty from '../../../components/ContentEmpty';
import CodeMirrorInput from '../../../components/CodeMirrorInput';

const entities = new AllHtmlEntities();

const HostNameDetailValue = styled.div`
  align-items: center;
  display: inline-grid;
  grid-gap: 10px;
  grid-template-columns: auto auto;
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
      isOpen={isOpen}
      onClose={onClose}
      title={i18n._(t`Host Details`)}
      aria-label={i18n._(t`Host details modal`)}
      width="75%"
    >
      <Tabs
        aria-label={i18n._(t`Tabs`)}
        activeKey={activeTabKey}
        onSelect={handleTabClick}
      >
        <Tab
          aria-label={i18n._(t`Details tab`)}
          eventKey={0}
          title={<TabTitleText>{i18n._(t`Details`)}</TabTitleText>}
        >
          <DetailList
            style={{ alignItems: 'center', marginTop: '20px' }}
            gutter="sm"
          >
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
          title={<TabTitleText>{i18n._(t`JSON`)}</TabTitleText>}
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
          title={<TabTitleText>{i18n._(t`Standard Out`)}</TabTitleText>}
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
          title={<TabTitleText>{i18n._(t`Standard Error`)}</TabTitleText>}
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
