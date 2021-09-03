import Ansi from 'ansi-to-html';
import hasAnsi from 'has-ansi';
import { encode } from 'html-entities';

const EVENT_START_TASK = 'playbook_on_task_start';
const EVENT_START_PLAY = 'playbook_on_play_start';
const EVENT_STATS_PLAY = 'playbook_on_stats';
const TIME_EVENTS = [EVENT_START_TASK, EVENT_START_PLAY, EVENT_STATS_PLAY];

const ansi = new Ansi({
  stream: true,
  colors: {
    0: '#000',
    1: '#A30000',
    2: '#486B00',
    3: '#795600',
    4: '#00A',
    5: '#A0A',
    6: '#004368',
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

function createStyleAttrHash(styleAttr) {
  let hash = 0;
  for (let i = 0; i < styleAttr.length; i++) {
    hash = (hash << 5) - hash; // eslint-disable-line no-bitwise
    hash += styleAttr.charCodeAt(i);
    hash &= hash; // eslint-disable-line no-bitwise
  }
  return `${hash}`;
}

const styleAttrPattern = new RegExp('style="[^"]*"', 'g');

function replaceStyleAttrs(html) {
  const allStyleAttrs = [...new Set(html.match(styleAttrPattern))];
  const cssMap = {};
  let result = html;
  for (let i = 0; i < allStyleAttrs.length; i++) {
    const styleAttr = allStyleAttrs[i];
    const cssClassName = `output-${createStyleAttrHash(styleAttr)}`;

    cssMap[cssClassName] = styleAttr.replace('style="', '').slice(0, -1);
    result = result.split(styleAttr).join(`class="${cssClassName}"`);
  }
  return { cssMap, result };
}

export default function getLineTextHtml({
  created,
  event,
  start_line: startLine,
  stdout,
}) {
  const sanitized = encode(stdout);
  let lineCssMap = {};
  const lineTextHtml = [];

  sanitized.split('\r\n').forEach((lineText, index) => {
    let html;
    if (hasAnsi(lineText)) {
      const { cssMap, result } = replaceStyleAttrs(ansi.toHtml(lineText));
      html = result;
      lineCssMap = { ...lineCssMap, ...cssMap };
    } else {
      html = lineText;
    }

    if (index === 1 && TIME_EVENTS.includes(event)) {
      const time = getTimestamp({ created });
      html += `<span class="time">${time}</span>`;
    }

    lineTextHtml.push({
      lineNumber: startLine + index,
      html,
    });
  });

  return {
    lineCssMap,
    lineTextHtml,
  };
}
