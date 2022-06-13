let ws;

export default function connectJobSocket({ type, id }, onMessage) {
  ws = new WebSocket(
    `${window.location.protocol === 'http:' ? 'ws:' : 'wss:'}//${
      window.location.host
    }${window.location.pathname}websocket/`
  );

  ws.onopen = () => {
    const xrftoken = `; ${document.cookie}`
      .split('; csrftoken=')
      .pop()
      .split(';')
      .shift();
    const eventGroup = `${type}_events`;
    ws.send(
      JSON.stringify({
        xrftoken,
        groups: { jobs: ['summary', 'status_changed'], [eventGroup]: [id] },
      })
    );
  };

  ws.onmessage = (e) => {
    onMessage(JSON.parse(e.data));
  };

  ws.onclose = (e) => {
    if (e.code !== 1000) {
      // eslint-disable-next-line no-console
      console.debug('Socket closed. Reconnecting...', e);
      setTimeout(() => {
        connectJobSocket({ type, id }, onMessage);
      }, 1000);
    }
  };

  ws.onerror = (err) => {
    // eslint-disable-next-line no-console
    console.debug('Socket error: ', err, 'Disconnecting...');
    ws.close();
  };
}

export function closeWebSocket() {
  if (ws) {
    ws.close();
  }
}
