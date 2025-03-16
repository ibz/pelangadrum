import random
import time

import adafruit_midi
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.timing_clock import TimingClock
from adafruit_midi.start import Start
from adafruit_midi.stop import Stop
from adafruit_midi.midi_continue import Continue
from pmk import PMK
from pmk.platform.keybow2040 import Keybow2040
import usb_midi

keybow = PMK(Keybow2040())

class Note:
    def __init__(self, pitch, velocity=100):
        self.pitch = pitch
        self.velocity = velocity

    def __eq__(self, other):
        if isinstance(other, Note):
            return self.pitch == other.pitch
        else:
            return self.pitch == other

class Step:
    def __init__(self, notes, duration):
        self.notes = notes
        self.duration = duration

class Sequence:
    def __init__(self):
        self.tonic = 33 + 12

    def generate(self):
        steps = []

        # pe-lan (0.15)
        steps.append(Step([Note(self.tonic)], 0.15))

        # ga (0.1)
        steps.append(Step([Note(self.tonic)], 0.1))

        # drum (0.1)
        if random.random() < 0.5:
            steps.append(Step([Note(self.tonic + 3), Note(self.tonic)], 0.1))
        else:
            steps.append(Step([Note(self.tonic + 7), Note(self.tonic + 3)], 0.1))

        # / (0.1)
        steps.append(Step([], 0.1))

        # (0.15)
        if random.random() < 0.3:
            # pe
            if random.random() < 0.8:
                steps.append(Step([Note(self.tonic)], 0.1))
            else:
                steps.append(Step([Note(self.tonic + 7)], 0.1))

            # lan
            steps.append(Step([Note(steps[-1].notes[0].pitch)], 0.05))
        else:
            # pe-lan
            if random.random() < 0.9:
                steps.append(Step([Note(self.tonic)], 0.15))
            else:
                steps.append(Step([Note(self.tonic + 7)], 0.15))

        # ga (0.1)
        steps.append(Step([Note(steps[-1].notes[0].pitch)], 0.1))

        # gard (0.1)
        if random.random() < 0.8:
            steps.append(Step([Note(self.tonic - 5), Note(self.tonic - 12)], 0.1))
        else:
            steps.append(Step([Note(self.tonic + 24)], 0.1))

        # / (0.1)
        steps.append(Step([], 0.1))

        return steps

class BassSequence:
    def __init__(self):
        self.tonic = 33
        self.i = 0

    def generate(self):
        steps = []
        steps.append(Step([Note(self.tonic - 24)], 0.25))
        steps.append(Step([Note(self.tonic + 3 - 24)], 0.1))
        steps.append(Step([], 0.1))
        if self.i == 0 or self.i == 2:
            steps.append(Step([Note(self.tonic - 24)], 0.25))
            steps.append(Step([Note(self.tonic - 5 - 24)], 0.1))
        elif self.i == 1:
            steps.append(Step([Note(self.tonic - 24 + 7)], 0.35))
        elif self.i == 3:
            steps.append(Step([Note(self.tonic - 24)], 0.35))
        steps.append(Step([], 0.1))
        self.i += 1
        if self.i > 3:
            self.i = 0
        return steps

class ClockType:
    INTERNAL = 0
    EXTERNAL = 1

class Performer:
    def __init__(self, sequence, bpm, midi, keybow, color):
        self.sequence = sequence
        self.bpm = bpm
        self.midi = midi
        self.keybow = keybow
        self.color = color
        self.polyphonic = True
        self.active = True

    def start(self):
        self._set_step = None
        self.start_time = time.monotonic()
        self.last_step_time = 0
        self.last_played = 0
        self.last_pulse_sent = 0
        if self.sequence:
            self.steps = self.sequence.generate()
        self.quarter_note_index = 0
        self.last_quarter_note_index = 0
        self.progress_in_bar = 0
        self.index = 0
        self.last_index = 0
        self.last_step = None
        self.pulses = 0

    def set_step(self, i):
        self._set_step = i

    def tick(self, monotonic):
        if not self.active:
            return

        if settings.clock_type == ClockType.INTERNAL:
            if monotonic - self.last_pulse_sent > 60 / self.bpm * WHOLE_NOTE / PPQN / 4:
                if self.pulses < PPWN:
                    #print("PULSE")
                    self.midi.send(TimingClock())
                    self.last_pulse_sent = monotonic
                    self.pulses += 1

        # TODO for external clock
        if self._set_step is not None:
            self.steps = self.sequence.generate()
            self.last_played = monotonic
            self.quarter_note_index = self._set_step
            bar_duration = sum(step.duration for step in self.steps)
            progress = 0
            for i, step in enumerate(self.steps):
                if progress >= bar_duration / 8 * self.quarter_note_index:
                    remaining = bar_duration / 8 * self.quarter_note_index - progress
                    self.index = i
                    self.last_step_time = 60 / self.bpm * remaining
                    break
                progress += step.duration
            self.last_step_time = 60 / self.bpm * self.steps[self.index].duration
            self.pulses = 0 ## ??
            self.progress_in_bar = progress
            self._set_step = None

        if monotonic - self.last_played > self.last_step_time:
            if self.index == len(self.steps):
                if settings.clock_type == ClockType.INTERNAL:
                    while self.pulses < PPWN:
                        #print("PULSE 2")
                        self.midi.send(TimingClock())
                        self.pulses += 1
                # TODO: self.start() ?
                self.quarter_note_index = 0
                self.index = 0
                self.pulses = 0
                self.steps = self.sequence.generate()
                self.progress_in_bar = 0

            if self.last_step:
                for i, note in enumerate(self.last_step.notes):
                    if i == 0 or self.polyphonic:
                        self.midi.send(NoteOff(note.pitch, 0))

            for i, note in enumerate(self.steps[self.index].notes):
                if i == 0 or self.polyphonic:
                    self.midi.send(NoteOn(note.pitch, note.velocity))

            bar_duration = sum(step.duration for step in self.steps)

            if settings.clock_type == ClockType.INTERNAL:
                current_duration = self.steps[self.index].duration
                self.progress_in_bar += current_duration
                bar_index = int(self.progress_in_bar / bar_duration * 8) - 1
                self.last_step_time = 60 / self.bpm * self.steps[self.index].duration
            elif settings.clock_type == ClockType.EXTERNAL:
                pulses_in_bar = 48
                current_duration = self.steps[self.index].duration
                bar_index = int(self.progress_in_bar / bar_duration * 8) - 1
                self.progress_in_bar += current_duration
                current_duration = current_duration / bar_duration * pulses_in_bar
                self.last_step_time = current_duration
                print("current_duration ", current_duration, "bar_index", bar_index)

            for i in range(8):
                if i == bar_index:
                    self.keybow.keys[i].set_led(*self.color)
                else:
                    self.keybow.keys[i].set_led(0, 0, 0)

            self.last_played = monotonic
            self.last_step = self.steps[self.index]
            self.last_index = self.index
            self.last_quarter_note_index = self.quarter_note_index
            self.index += 1
            self.quarter_note_index += 1
            return self.last_index

def dec5(performers, _):
    for p in performers:
        p.bpm -= 5

def inc5(performers, _):
    for p in performers:
        p.bpm += 5

def ocdn(performers, _):
    for p in performers:
        p.sequence.tonic -= 12

def ocup(performers, _):
    for p in performers:
        p.sequence.tonic += 12

def step(i):
    def stepi(performers, _):
        for p in performers:
            p.set_step(i)
    return stepi

def monopoly(performers, _):
    for p in performers:
        p.polyphonic = not p.polyphonic

def intext(performers, settings):
    if settings.clock_type == ClockType.INTERNAL:
        settings.clock_type = ClockType.EXTERNAL
    else:
        settings.clock_type = ClockType.INTERNAL
    for p in performers:
        p.start()

def dropmainline(performers, _):
    performers.pop(0)

def dropbass(performers, _):
    performers.pop()

KEYS = [step(0), step(1), step(2), step(3),
        step(4), step(5), step(6), step(7),
        dropmainline, dropbass, monopoly, intext,
        dec5, inc5, ocdn, ocup]

for key in keybow.keys:
    @keybow.on_press(key)
    def press(key):
        global performers
        global settings
        f = KEYS[key.number]
        if f is not None:
            f(performers, settings)

keybow.keys[8].set_led(255, 255, 0)
keybow.keys[9].set_led(255, 0, 0)
keybow.keys[10].set_led(128, 128, 255)
keybow.keys[11].set_led(0, 0, 255)
keybow.keys[12].set_led(255, 0, 0)
keybow.keys[13].set_led(0, 255, 0)

performer = Performer(Sequence(), 30, adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0), keybow, (255, 255, 0))
performer.start()

bass_performer = Performer(BassSequence(), 30, adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=1), keybow, (255, 0, 0))
bass_performer.start()

class Settings:
    def __init__(self):
        self.clock_type = ClockType.INTERNAL

settings = Settings()
performers = [performer, bass_performer]

WHOLE_NOTE = 1 # 0.9 # WTF
PPQN = 24 # MIDI standard
PPWN = PPQN * 4

midi_in = adafruit_midi.MIDI(midi_in=usb_midi.ports[0], in_channel=None)

clock_counter = 0

while True:
    keybow.update() # always remember to call keybow.update()!

    if settings.clock_type == ClockType.INTERNAL:

        monotonic = time.monotonic()

        indices = []
        for i, p in enumerate(performers):
            index = p.tick(monotonic)
            indices.append(index)

        # when any of the performers arrived at the beginning of the sequence,
        # we allow all others to advance until they also arrive there
        while 0 in indices and any(index != 0 for index in indices):
            monotonic = time.monotonic()
            for i, p in enumerate(performers):
                if indices[i] != 0:
                    index = p.tick(monotonic)
                    indices[i] = index
    elif settings.clock_type == ClockType.EXTERNAL:
        msg = midi_in.receive()
        if msg:
            if isinstance(msg, Start) or isinstance(msg, Continue):
                print("MIDI Clock Started")
                clock_counter = 0
            elif isinstance(msg, Stop):
                print("MIDI Clock Stopped")
            elif isinstance(msg, TimingClock):
                print("GOT CLOCK")
                clock_counter += 1
                for p in performers:
                    p.tick(clock_counter)

