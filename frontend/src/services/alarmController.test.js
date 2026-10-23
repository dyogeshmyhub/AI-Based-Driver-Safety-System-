import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ALARM_MODES, AlarmController, getAlarmMode } from './alarmController';

function createAudioContextMock() {
  const oscillators = [];
  const gains = [];
  const context = {
    state: 'running',
    currentTime: 0,
    destination: {},
    oscillators,
    gains,
    createOscillator: vi.fn(() => {
      const oscillator = {
        type: '',
        frequency: { setValueAtTime: vi.fn() },
        connect: vi.fn(),
        start: vi.fn(),
        stop: vi.fn(),
        disconnect: vi.fn(),
        onended: null,
      };
      oscillators.push(oscillator);
      return oscillator;
    }),
    createGain: vi.fn(() => {
      const node = {
        gain: {
          setValueAtTime: vi.fn(),
          linearRampToValueAtTime: vi.fn(),
        },
        connect: vi.fn(),
        disconnect: vi.fn(),
      };
      gains.push(node);
      return node;
    }),
    resume: vi.fn(() => Promise.resolve()),
    close: vi.fn(() => Promise.resolve()),
  };

  return context;
}

beforeEach(() => vi.useFakeTimers());
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe('getAlarmMode', () => {
  it('does not alarm for a normal blink or while monitoring is stopped', () => {
    expect(getAlarmMode({
      monitoring: true,
      eyeState: 'CLOSED',
      drowsinessState: 'ALERT',
      yawnCount: 0,
      mouthState: 'CLOSED',
    })).toBe(ALARM_MODES.NORMAL);
    expect(getAlarmMode({ monitoring: false, eyeState: 'CLOSED', drowsinessState: 'CRITICAL' }))
      .toBe(ALARM_MODES.NORMAL);
  });

  it('selects prolonged closure and repeated yawning, prioritizing eye closure', () => {
    expect(getAlarmMode({
      monitoring: true,
      eyeState: 'CLOSED',
      drowsinessState: 'WARNING',
      yawnCount: 0,
      mouthState: 'OPEN',
    })).toBe(ALARM_MODES.EYE_CLOSURE);
    expect(getAlarmMode({
      monitoring: true,
      eyeState: 'CLOSED',
      drowsinessState: 'WARNING',
      yawnCount: 1,
      mouthState: 'OPEN',
      singleYawnPending: true,
    })).toBe(ALARM_MODES.EYE_CLOSURE);
    expect(getAlarmMode({
      monitoring: true,
      eyeState: 'OPEN',
      drowsinessState: 'ALERT',
      yawnCount: 2,
      mouthState: 'OPEN',
      repeatedYawnPending: true,
    })).toBe(ALARM_MODES.REPEATED_YAWNING);
    expect(getAlarmMode({
      monitoring: true,
      eyeState: 'OPEN',
      drowsinessState: 'ALERT',
      yawnCount: 2,
      mouthState: 'OPEN',
      repeatedYawnPending: false,
    })).toBe(ALARM_MODES.NORMAL);
  });

  it('uses a single-yawn alert and clears it when the mouth is normal', () => {
    expect(getAlarmMode({
      monitoring: true,
      eyeState: 'OPEN',
      drowsinessState: 'ALERT',
      yawnCount: 1,
      mouthState: 'OPEN',
      singleYawnPending: true,
    })).toBe(ALARM_MODES.YAWN);
    expect(getAlarmMode({
      monitoring: true,
      eyeState: 'OPEN',
      drowsinessState: 'ALERT',
      yawnCount: 1,
      mouthState: 'CLOSED',
      singleYawnPending: false,
    })).toBe(ALARM_MODES.NORMAL);
  });
});

describe('AlarmController', () => {
  it('plays one continuous four-second alert for a prolonged eye closure', () => {
    const context = createAudioContextMock();
    vi.stubGlobal('window', {
      AudioContext: vi.fn(() => context),
      setTimeout: globalThis.setTimeout,
      clearTimeout: globalThis.clearTimeout,
    });
    const controller = new AlarmController();
    controller.unlock();

    controller.setMode(ALARM_MODES.EYE_CLOSURE);
    expect(context.oscillators).toHaveLength(1);
    expect(context.oscillators[0].start).toHaveBeenCalledWith(0);
    expect(context.oscillators[0].stop).toHaveBeenCalledWith(4);
    expect(context.gains[0].gain.setValueAtTime).toHaveBeenCalledTimes(19);
    expect(context.gains[0].gain.linearRampToValueAtTime).toHaveBeenCalledTimes(18);

    controller.setMode(ALARM_MODES.EYE_CLOSURE);
    expect(context.oscillators).toHaveLength(1);

    vi.advanceTimersByTime(5499);
    expect(context.oscillators).toHaveLength(1);
    vi.advanceTimersByTime(1);
    expect(context.oscillators).toHaveLength(2);
    expect(context.oscillators[1].stop).toHaveBeenCalledWith(4);

    controller.setMode(ALARM_MODES.NORMAL);
    vi.advanceTimersByTime(10000);
    expect(context.oscillators).toHaveLength(2);
    controller.dispose();
    expect(context.close).toHaveBeenCalledOnce();
    expect(context.oscillators[1].stop).toHaveBeenCalled();
  });

  it('plays one alert per yawn and can alert again after the mouth resets', () => {
    const context = createAudioContextMock();
    vi.stubGlobal('window', {
      AudioContext: vi.fn(() => context),
      setTimeout: globalThis.setTimeout,
      clearTimeout: globalThis.clearTimeout,
    });
    const controller = new AlarmController();
    controller.unlock();

    controller.setMode(ALARM_MODES.YAWN);
    controller.setMode(ALARM_MODES.YAWN);
    expect(context.oscillators).toHaveLength(1);
    expect(context.oscillators[0].stop).toHaveBeenCalledWith(4);

    controller.setMode(ALARM_MODES.NORMAL);
    controller.setMode(ALARM_MODES.YAWN);
    expect(context.oscillators).toHaveLength(2);
    controller.dispose();
  });

  it('stops the current alert before switching modes so warnings never overlap', () => {
    const context = createAudioContextMock();
    vi.stubGlobal('window', {
      AudioContext: vi.fn(() => context),
      setTimeout: globalThis.setTimeout,
      clearTimeout: globalThis.clearTimeout,
    });
    const controller = new AlarmController();
    controller.unlock();

    controller.setMode(ALARM_MODES.EYE_CLOSURE);
    controller.setMode(ALARM_MODES.YAWN);

    expect(context.oscillators).toHaveLength(2);
    expect(context.oscillators[0].stop).toHaveBeenCalledTimes(2);
    expect(context.oscillators[1].start).toHaveBeenCalledOnce();

    controller.endMonitoring();
    expect(context.oscillators[1].stop).toHaveBeenCalled();
    expect(context.close).toHaveBeenCalledOnce();
  });

  it('restarts audio after monitoring starts again', () => {
    const firstContext = createAudioContextMock();
    const secondContext = createAudioContextMock();
    const contexts = [firstContext, secondContext];
    vi.stubGlobal('window', {
      AudioContext: vi.fn(() => contexts.shift()),
      setTimeout: globalThis.setTimeout,
      clearTimeout: globalThis.clearTimeout,
    });
    const controller = new AlarmController();

    controller.unlock();
    controller.setMode(ALARM_MODES.EYE_CLOSURE);
    controller.endMonitoring();
    controller.unlock();
    controller.setMode(ALARM_MODES.EYE_CLOSURE);

    expect(firstContext.oscillators[0].stop).toHaveBeenCalled();
    expect(secondContext.oscillators).toHaveLength(1);
    controller.dispose();
  });
});
