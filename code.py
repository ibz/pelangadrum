import random
import time

import adafruit_midi
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.timing_clock import TimingClock
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
        self.tonic = 31 + 12

    def generate(self):
        steps = []
        steps.append(Step([Note(self.tonic)], 0.15))
        steps.append(Step([Note(self.tonic)], 0.1))
        if random.random() < 0.5:
            steps.append(Step([Note(self.tonic + 3), Note(self.tonic)], 0.1))
        else:
            steps.append(Step([Note(self.tonic + 7), Note(self.tonic + 3)], 0.1))
        steps.append(Step([], 0.1))
        if random.random() < 0.3:
            if random.random() < 0.8:
                steps.append(Step([Note(self.tonic)], 0.1))
            else:
                steps.append(Step([Note(self.tonic + 7)], 0.1))
            steps.append(Step([Note(steps[-1].notes[0].pitch)], 0.05))
        else:
            if random.random() < 0.9:
                steps.append(Step([Note(self.tonic)], 0.15))
            else:
                steps.append(Step([Note(self.tonic + 7)], 0.15))
        steps.append(Step([Note(steps[-1].notes[0].pitch)], 0.1))
        if random.random() < 0.8:
            steps.append(Step([Note(self.tonic - 5), Note(self.tonic - 12)], 0.1))
        else:
            steps.append(Step([Note(self.tonic + 24)], 0.1))
        steps.append(Step([], 0.1))
        return steps

class BassSequence:
    def __init__(self):
        self.tonic = 31
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

class Performer:
    def __init__(self, sequence, bpm, midi, keybow, color):
        self.sequence = sequence
        self.bpm = bpm
        self.midi = midi
        self.keybow = keybow
        self.color = color
        self.polyphonic = True

    def start(self):
        self.start_time = time.monotonic()
        self.last_step_time = 0
        self.last_played = 0
        self.last_pulse_sent = 0
        if self.sequence:
            self.steps = self.sequence.generate()
        self.index = 0
        self.last_index = 0
        self.last_step = None
        self.pulses = 0

    def tick(self, monotonic):
        if monotonic - self.last_pulse_sent > 60 / self.bpm * WHOLE_NOTE / PPQN / 4:
            if self.pulses < PPWN:
                self.midi.send(TimingClock())
                self.last_pulse_sent = monotonic
                self.pulses += 1
        if monotonic - self.last_played > self.last_step_time:
            if self.index == len(self.steps):
                while self.pulses < PPWN:
                    self.midi.send(TimingClock())
                    self.pulses += 1
                self.index = 0
                self.pulses = 0
                self.steps = self.sequence.generate()

            if self.last_step:
                for i, note in enumerate(self.last_step.notes):
                    if i == 0 or self.polyphonic:
                        self.midi.send(NoteOff(note.pitch, 0))
                self.keybow.keys[self.last_index].set_led(0, 0, 0)

            for i, note in enumerate(self.steps[self.index].notes):
                if i == 0 or self.polyphonic:
                    self.midi.send(NoteOn(note.pitch, note.velocity))

            self.keybow.keys[self.index].set_led(*self.color)

            self.last_played = monotonic
            self.last_step = self.steps[self.index]
            self.last_step_time = 60 / self.bpm * self.steps[self.index].duration
            self.last_index = self.index
            self.index += 1
            return self.last_index

for key in keybow.keys:
    @keybow.on_press(key)
    def press(key):
        global performers
        if key.number in (0, 1):
            performers[key.number].polyphonic = not performers[key.number].polyphonic
        for performer in performers:
            if key.number == 12:
                performer.bpm -= 5
            elif key.number == 13:
                performer.bpm += 5
            elif key.number == 8:
                performer.bpm -= 1
            elif key.number == 9:
                performer.bpm += 1
            elif key.number == 14:
                performer.sequence.tonic -= 12
            elif key.number == 15:
                performer.sequence.tonic += 12

keybow.keys[8].set_led(128, 0, 0)
keybow.keys[9].set_led(0, 128, 0)
keybow.keys[12].set_led(255, 0, 0)
keybow.keys[13].set_led(0, 255, 0)

performer = Performer(Sequence(), 30, adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=0), keybow, (255, 255, 0))
performer.start()

bass_performer = Performer(BassSequence(), 30, adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=1), keybow, (255, 0, 0))
bass_performer.start()

performers = [performer, bass_performer]

WHOLE_NOTE = 0.9 # WTF
PPQN = 24 # MIDI standard
PPWN = PPQN * 4

while True:
    keybow.update() # always remember to call keybow.update()!

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
