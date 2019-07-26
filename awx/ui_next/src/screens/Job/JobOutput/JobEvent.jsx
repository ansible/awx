import Ansi from 'ansi-to-html';
import hasAnsi from 'has-ansi';
import Entities from 'html-entities';
import styled from 'styled-components';
import React from 'react';

const EVENT_START_TASK = 'playbook_on_task_start';
const EVENT_START_PLAY = 'playbook_on_play_start';
const EVENT_STATS_PLAY = 'playbook_on_stats';
const TIME_EVENTS = [EVENT_START_TASK, EVENT_START_PLAY, EVENT_STATS_PLAY];

const ansi = new Ansi({
  stream: true,
  colors: {
    0: '#000',
    1: '#A00',
    2: '#080',
    3: '#F0AD4E',
    4: '#00A',
    5: '#A0A',
    6: '#0AA',
    7: '#AAA',
    8: '#555',
    9: '#F55',
    10: '#5F5',
    11: '#FF5',
    12: '#55F',
    13: '#F5F',
    14: '#5FF',
    15: '#FFF',
  },
});
const entities = new Entities.AllHtmlEntities();

const JobEventWrapper = styled.div``;
const JobEventLine = styled.div`
  display: flex;

  &:hover {
    background-color: white;
  }

  &:hover div {
    background-color: white;
  }

  &--hidden {
    display: none;
  }
  ${({ isFirst }) => (isFirst ? 'padding-top: 10px;' : '')}
`;
const JobEventLineToggle = styled.div`
  background-color: #ebebeb;
  color: #646972;
  display: flex;
  flex: 0 0 30px;
  font-size: 18px;
  justify-content: center;
  line-height: 12px;

  & > i {
    cursor: pointer;
  }

  user-select: none;
`;
const JobEventLineNumber = styled.div`
  color: #161b1f;
  background-color: #ebebeb;
  flex: 0 0 45px;
  text-align: right;
  vertical-align: top;
  padding-right: 5px;
  border-right: 1px solid #d7d7d7;
  user-select: none;
`;
const JobEventLineText = styled.div`
  padding: 0 15px;
  white-space: pre-wrap;
  word-break: break-all;
  word-wrap: break-word;

  .time {
    font-size: 14px;
    font-weight: 600;
    user-select: none;
    background-color: #ebebeb;
    border-radius: 12px;
    padding: 2px 10px;
    margin-left: 15px;
  }
`;

function getTimestamp({ created }) {
  const date = new Date(created);

  const dateHours = date.getHours();
  const dateMinutes = date.getMinutes();
  const dateSeconds = date.getSeconds();

  const stampHours = dateHours < 10 ? `0${dateHours}` : dateHours;
  const stampMinutes = dateMinutes < 10 ? `0${dateMinutes}` : dateMinutes;
  const stampSeconds = dateSeconds < 10 ? `0${dateSeconds}` : dateSeconds;

  return `${stampHours}:${stampMinutes}:${stampSeconds}`;
}

function getLineTextHtml({ created, event, start_line, stdout }) {
  const sanitized = entities.encode(stdout);
  return sanitized.split('\r\n').map((lineText, index) => {
    let html;
    if (hasAnsi(lineText)) {
      html = ansi.toHtml(lineText);
    } else {
      html = lineText;
    }

    if (index === 1 && TIME_EVENTS.includes(event)) {
      const time = getTimestamp({ created });
      html += `<span class="time">${time}</span>`;
    }

    return {
      lineNumber: start_line + index,
      html,
    };
  });
}

function JobEvent({ counter, created, event, stdout, start_line, ...rest }) {
  return !stdout ? null : (
    <JobEventWrapper {...rest}>
      {getLineTextHtml({ created, event, start_line, stdout }).map(
        ({ lineNumber, html }) =>
          lineNumber >= 0 && (
            <JobEventLine
              key={`${counter}-${lineNumber}`}
              isFirst={lineNumber === 0}
            >
              <JobEventLineToggle />
              <JobEventLineNumber>{lineNumber}</JobEventLineNumber>
              <JobEventLineText
                dangerouslySetInnerHTML={{
                  __html: html,
                }}
              />
            </JobEventLine>
          )
      )}
    </JobEventWrapper>
  );
}

export default JobEvent;
