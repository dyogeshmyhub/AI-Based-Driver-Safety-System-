const WARNING_DURATION_SECONDS = 4;
const WARNING_COOLDOWN_MS = 1500;
const BEEP_INTERVAL_SECONDS = 0.45;
const BEEP_DURATION_SECONDS = 0.2;
const BEEP_VOLUME = 0.22;

export const ALARM_MODES = {
  NORMAL: 'NORMAL',
  EYE_CLOSURE: 'EYE_CLOSURE',
  REPEATED_YAWNING: 'REPEATED_YAWNING',
  YAWN: 'YAWN',
};

export function getAlarmMode({
  monitoring,
  eyeState,
  drowsinessState,
  yawnCount,
  mouthState,
  singleYawnPending,
  repeatedYawnPending,
}) {
  if (!monitoring) return ALARM_MODES.NORMAL;

  const eyesClosed = String(eyeState || '').toUpperCase() === 'CLOSED';
  const drowsy = ['WARNING', 'DROWSY', 'CRITICAL'].includes(String(drowsinessState || '').toUpperCase());
  const mouth = String(mouthState || '').toUpperCase();
  const mouthIsNormal = mouth === 'CLOSED' || mouth === 'MOUTH CLOSED' || mouth === 'NORMAL';

  if (eyesClosed && drowsy) return ALARM_MODES.EYE_CLOSURE;
  if (Number(yawnCount) >= 2 && repeatedYawnPending && !mouthIsNormal) return ALARM_MODES.REPEATED_YAWNING;
  if (singleYawnPending) return ALARM_MODES.YAWN;
  return ALARM_MODES.NORMAL;
}

export class AlarmController {
  constructor() {
    this.context = null;
    this.mode = ALARM_MODES.NORMAL;
    this.repeatTimer = null;
    this.activeOscillator = null;
    this.audioWarningShown = false;
    this.disposed = false;
  }

  unlock() {
    if (this.disposed) return;

    try {
      if (!this.context) {
        const AudioContextClass = window.AudioContext;
        if (!AudioContextClass) {
          this.warnAudioUnavailable();
          return;
        }
        this.context = new AudioContextClass();
      }

      if (this.context.state === 'suspended') {
        this.context.resume().catch((error) => {
          console.warn('Unable to unlock driver warning audio:', error);
        });
      }
    } catch (error) {
      console.warn('Unable to initialize driver warning audio:', error);
    }
  }

  setMode(mode) {
    if (!Object.values(ALARM_MODES).includes(mode)) {
      throw new Error(`Unsupported alarm mode: ${mode}`);
    }
    if (this.disposed || this.mode === mode) return;

    this.clearRepeatTimer();
    this.stopTone();
    this.mode = mode;
    if (mode === ALARM_MODES.NORMAL) return;

    this.playWarning();
  }

  endMonitoring() {
    this.setMode(ALARM_MODES.NORMAL);
    this.clearRepeatTimer();
    this.stopTone();

    if (this.context) {
      const context = this.context;
      this.context = null;
      context.close().catch((error) => {
        console.warn('Unable to close driver warning audio:', error);
      });
    }
  }

  dispose() {
    this.endMonitoring();
    this.disposed = true;
  }

  clearRepeatTimer() {
    if (this.repeatTimer !== null) {
      window.clearTimeout(this.repeatTimer);
      this.repeatTimer = null;
    }
  }

  scheduleRepeat() {
    this.repeatTimer = window.setTimeout(() => {
      this.repeatTimer = null;
      if (this.disposed || this.mode === ALARM_MODES.NORMAL) return;
      this.stopTone();
      this.playWarning();
    }, WARNING_DURATION_SECONDS * 1000 + WARNING_COOLDOWN_MS);
  }

  playWarning() {
    if (!this.context || this.activeOscillator) return;
    if (this.context.state !== 'running') {
      if (this.context.state === 'suspended') {
        const context = this.context;
        const retryPlayback = () => {
          if (this.context === context && this.mode !== ALARM_MODES.NORMAL && !this.disposed) {
            this.playWarning();
          }
        };
        const reportResumeError = (error) => {
          console.warn('Unable to resume driver warning audio:', error);
        };
        try {
          context.resume().then(retryPlayback).catch(reportResumeError);
        } catch (error) {
          reportResumeError(error);
        }
      }
      return;
    }

    try {
      const context = this.context;
      const oscillator = context.createOscillator();
      const gain = context.createGain();
      const now = context.currentTime;

      oscillator.type = 'square';
      oscillator.frequency.setValueAtTime(880, now);
      gain.gain.setValueAtTime(0.0001, now);
      for (let beepStart = 0; beepStart < WARNING_DURATION_SECONDS; beepStart += BEEP_INTERVAL_SECONDS) {
        const start = now + beepStart;
        gain.gain.setValueAtTime(0.0001, start);
        gain.gain.linearRampToValueAtTime(BEEP_VOLUME, start + 0.01);
        gain.gain.setValueAtTime(BEEP_VOLUME, start + BEEP_DURATION_SECONDS - 0.01);
        gain.gain.linearRampToValueAtTime(0.0001, start + BEEP_DURATION_SECONDS);
      }

      oscillator.connect(gain);
      gain.connect(context.destination);
      oscillator.onended = () => {
        oscillator.disconnect();
        gain.disconnect();
        if (this.activeOscillator === oscillator) this.activeOscillator = null;
      };
      this.activeOscillator = oscillator;
      oscillator.start(now);
      oscillator.stop(now + WARNING_DURATION_SECONDS);
      this.scheduleRepeat();
    } catch (error) {
      this.clearRepeatTimer();
      this.stopTone();
      console.warn('Unable to play driver warning audio:', error);
    }
  }

  stopTone() {
    if (!this.activeOscillator) return;

    const oscillator = this.activeOscillator;
    this.activeOscillator = null;
    oscillator.onended = null;
    try {
      oscillator.stop();
    } catch (error) {
      if (error.name !== 'InvalidStateError') {
        console.warn('Unable to stop driver warning audio:', error);
      }
    }
    oscillator.disconnect();
  }

  warnAudioUnavailable() {
    if (this.audioWarningShown) return;
    this.audioWarningShown = true;
    console.warn('Driver warning audio is unavailable because this browser does not support AudioContext.');
  }
}
