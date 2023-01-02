import time
from pmk import PMK
from pmk.platform.keybow2040 import Keybow2040 as Hardware          # for Keybow 2040
# from pmk.platform.rgbkeypadbase import RGBKeypadBase as Hardware  # for Pico RGB Keypad Base

import usb_midi
import adafruit_midi
from adafruit_midi.note_off import NoteOff
from adafruit_midi.note_on import NoteOn

# Set up Keybow
keybow = PMK(Hardware())
keys = keybow.keys

# Set USB MIDI up on channel 0.
midi = adafruit_midi.MIDI(midi_out=usb_midi.ports[1], out_channel=5)

# The colour to set the keys when pressed, orange-y.
rgb = (255, 50, 0)

# MIDI velocity.
start_note = 36
velocity = 100

# Beats per minute
bpm = 80

# Play 16th notes
note_length = 1 / 16

# Assumes BPM is calculated on quarter notes
note_time = 60 / bpm * (note_length * 4)

direction = 1

# Keep track of time of last note played and last keys pressed
last_played = 0
last_pressed = []

notes = [start_note, start_note, start_note, start_note + 3, start_note, start_note, start_note, start_note - 5]
this_note = last_note = 0

while True:
    # Always remember to call keybow.update()!
    keybow.update()

    # If the currently pressed notes are the same as the last loop, then...

    if notes != []:
        # Check time elapsed since last note played
        elapsed = time.monotonic() - last_played

        # If the note time has elapsed, then...
        if elapsed > note_time:
            # Reset at the end or start of the notes list
            if this_note == len(notes) and direction == 1:
                this_note = 0
            elif this_note < 0:
                this_note = len(notes) - 1

            # Send a MIDI note off for the last note, turn off LED
            midi.send(NoteOff(notes[last_note], 0))
            #keys[notes[last_note - start_note]].set_led(0, 0, 0)

            # Send a MIDI note on for the next note, turn on LED
            midi.send(NoteOn(notes[this_note], velocity))
            #keys[notes[this_note - start_note]].set_led(*rgb)

            # Update time last_played, make this note last note
            last_played = time.monotonic()
            last_note = this_note
            
            this_note += direction

