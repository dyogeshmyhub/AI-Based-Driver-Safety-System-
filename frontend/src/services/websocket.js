const WS_URL = import.meta.env.VITE_WS_URL || 'ws://127.0.0.1:8000/ws/monitoring';

export class MonitoringSocket {
  constructor({ onState, onStatus }) {
    this.onState = onState;
    this.onStatus = onStatus;
    this.socket = null;
    this.closedByUser = false;
    this.retryTimer = null;
    this.retryDelay = 1000;
  }

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }
    this.closedByUser = false;
    this.onStatus('CONNECTING');
    this.socket = new WebSocket(WS_URL);
    this.socket.onopen = () => {
      this.retryDelay = 1000;
      this.onStatus('CONNECTED');
    };
    this.socket.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'monitoring_update') {
          this.onState(payload);
          this.onStatus('CONNECTED');
        }
      } catch {
        this.onStatus('ERROR');
      }
    };
    this.socket.onerror = () => this.onStatus('ERROR');
    this.socket.onclose = () => {
      this.socket = null;
      if (!this.closedByUser) {
        this.onStatus('RECONNECTING');
        this.retryTimer = window.setTimeout(() => this.connect(), this.retryDelay);
        this.retryDelay = Math.min(this.retryDelay * 2, 10000);
      } else {
        this.onStatus('DISCONNECTED');
      }
    };
  }

  disconnect() {
    this.closedByUser = true;
    if (this.retryTimer) window.clearTimeout(this.retryTimer);
    if (this.socket) this.socket.close();
    this.socket = null;
    this.onStatus('DISCONNECTED');
  }
}

export { WS_URL };
