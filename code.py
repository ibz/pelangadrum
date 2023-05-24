import random
import time

from pmk import PMK
from pmk.platform.keybow2040 import Keybow2040 as Hardware

import usb_midi
import adafruit_midi
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn
from adafruit_midi.timing_clock import TimingClock

keybow = PMK(Hardware())
keys = keybow.keys

# Set USB MIDI up on channel 0.
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1])

# The colour to set the keys when pressed, orange-y.
rgb = (255, 255, 0)

# MIDI velocity.
start_note = 31
velocity = 100

bpm = 30

last_pulse_sent = 0
last_played = 0
last_pressed = []

class M:
    def notes(self):
        return [(start_note, 0.15),
                (start_note, 0.1),
                (lambda prev: [start_note + 0, start_note + 3] if random.random() < 0.5 else [start_note + 3, start_note + 7], 0.1),
                (0, 0.1)
                ] + \
              ([
                (lambda prev: start_note if (start_note in prev or random.random() < 0.8) else start_note + 7, 0.1),
                (lambda prev: prev[0], 0.05)] if random.random() < 0.3 else [
                    (lambda prev: start_note if start_note not in prev and random.random() < 0.9 else start_note + 7, 0.15)]) + \
               [(lambda prev: prev[0], 0.1),
                (lambda prev: [start_note - 12, start_note - 5] if random.random() < 0.8 else [start_note + 24], 0.1),
                (0, 0.1)]

this_note = last_note = 0

last_note_time = 0
last_note_pitches = []

melody = M()

notes = melody.notes()

for key in keys:
    @keybow.on_press(key)
    def press(key):
        global bpm, start_note
        if key.number == 12:
            bpm -= 5
        elif key.number == 13:
            bpm += 5
        elif key.number == 8:
            bpm -= 1
        elif key.number == 9:
            bpm += 1
        elif key.number == 14:
            start_note -= 12
        elif key.number == 15:
            start_note += 12
            print(key.number)

keys[8].set_led(128, 0, 0)
keys[9].set_led(0, 128, 0)
keys[12].set_led(255, 0, 0)
keys[13].set_led(0, 255, 0)

def ms_per_tick():
  return 60000 / (bpm * 24)
tp = 0

WHOLE_NOTE = 0.9 # WTF

PPQN = 24 # MIDI standard
PPWN = PPQN * 4

pulses = 0

while True:
    # Always remember to call keybow.update()!
    keybow.update()
    
    monot = time.monotonic()
    elapsed = monot - last_played
    pulse_elapsed = monot - last_pulse_sent

    whole_note_time = 60 / bpm * WHOLE_NOTE

    if pulse_elapsed > whole_note_time / PPQN / 4:
        if pulses < PPQN * 4:
            midi.send(TimingClock())
            last_pulse_sent = time.monotonic()
            pulses += 1
            print("|" + str(pulses))
        else:
            print("?")

    if elapsed > last_note_time:
        if this_note == len(notes):
            while pulses < PPQN * 4:
                midi.send(TimingClock())
                print("+" + str(pulses))
                pulses += 1
            this_note = 0
            pulses = 0
            notes = melody.notes()
            print("")

        this_note_pitches, this_note_length = notes[this_note]
        
        this_note_time = 60 / bpm * (this_note_length)

        if callable(this_note_pitches):
            this_note_pitches = this_note_pitches(last_note_pitches)

        if not isinstance(this_note_pitches, list):
            this_note_pitches = [this_note_pitches]

        for p in last_note_pitches:
            if p:
                midi.send(NoteOff(p, 0))

        keys[last_note].set_led(0,0,0)

        for p in this_note_pitches:
            if p != 0:
                midi.send(NoteOn(p, velocity))
            keys[this_note].set_led(*rgb)

        # Update time last_played, make this note last note
        last_played = time.monotonic()
        last_note_pitches = this_note_pitches
        last_note_time = this_note_time
        last_note = this_note
        this_note += 1

