use_bpm 40

def pelangagard(use_synth: :pluck, base_note: :c5, base_amp: 1)
  synth use_synth, note: base_note, amp: base_amp * 0.5, release: 0.08
  sleep 0.08
  synth use_synth, note: base_note, amp: base_amp * 0.5, release: 0.12
  sleep 0.12
  synth use_synth, note: base_note, amp: base_amp, release: 0.1
  sleep 0.1
  how = [:low, :high].sample
  delta_1, delta_2 = how == :low ? [0, 3] : [3, 7]
  synth use_synth, note: base_note + delta_1, attack: 0, release: 0.1, amp: base_amp * 0.7
  synth use_synth, note: base_note + delta_2, attack: 0, release: 0.1, amp: base_amp * 2
  sleep 0.2

  how = :normal unless how == :high and one_in(7)
  delta = how == :normal ? 0 : 7

  synth use_synth, note: base_note + delta, amp: base_amp * 0.7, release: 0.05
  sleep 0.05
  if one_in(3)
    synth use_synth, note: base_note + delta, amp: base_amp * 0.7, release: 0.1
    sleep 0.1
    synth use_synth, note: base_note + delta, amp: base_amp * 0.7, release: 0.05
    sleep 0.05
  else
    synth use_synth, note: base_note + delta, amp: base_amp * 0.7, release: 0.15
    sleep 0.15
  end
  synth use_synth, note: base_note + delta, amp: base_amp, release: 0.1
  sleep 0.1
  if one_in(7)
    synth use_synth, note: base_note, attack: 0, release: 0.1, amp: base_amp * 2
    sleep 0.2
  else
    synth use_synth, note: base_note - 12, attack: 0, release: 0.1, amp: base_amp * 2
    synth use_synth, note: base_note - 5, attack: 0, release: 0.1, amp: base_amp
    sleep 0.2
  end
end

def ah_ce_dor(base_amp=1, phase=4)
  if tick % phase == 0
    if one_in(3)
      with_fx :pitch_shift, pitch: 4 do
        sample "/home/ibz/Samples/dor.ogg", amp:base_amp
      end
    else
      sample "/home/ibz/Samples/dor.ogg", amp:base_amp
    end
  end
end

def bas(use_synth: :saw, amp: 0.5, base_note: :c2)
  synth use_synth, note: base_note, attack: 0, release: 0.1, amp: amp
  sleep 0.3
  synth use_synth, note: base_note + 7, attack: 0, release: 0.1, amp: amp
  sleep 0.2
  
  synth use_synth, note: base_note, attack: 0, release: 0.1, amp: amp
  sleep 0.3
  synth use_synth, note: base_note - 12, attack: 0, release: 0.1, amp: amp
  sleep 0.2
end

def toba(use_sample_1: :bd_ada, use_sample_2: :bd_tek, base_amp: 1, accent: 1)
  has_var = false
  if one_in(3)
    has_var = true
    sample use_sample_1, amp: base_amp * (0.5)
    sleep 0.05
    sample use_sample_1, amp: base_amp * (0.5)
    sleep 0.05
    sample use_sample_1, amp: base_amp * ([1, 3].include?(accent) ? 2 : 0.5)
    sleep 0.2
  else
    sample use_sample_1, amp: base_amp * ([1, 3].include?(accent) ? 2 : 0.5)
    sleep 0.3
  end
  
  sample use_sample_2, amp: base_amp * ([2, 3].include?(accent) ? 2 : 0.5)
  sleep 0.2
  
  sample use_sample_1, amp: base_amp * ([1, 3].include?(accent) ? 2 : 0.5)
  sleep 0.3
  
  if one_in(3) and not has_var
    sample use_sample_2, amp: base_amp * ([2, 3].include?(accent) ? 2 : 0.5)
    sleep 0.1
    sample use_sample_2, amp: base_amp * ([2, 3].include?(accent) ? 2 : 0.5)
    sleep 0.1
  else
    sample use_sample_2, amp: base_amp * ([2, 3].include?(accent) ? 2 : 0.5)
    sleep 0.2
  end
end

live_loop :sega do
  # pluck | c5
  pelangagard(use_synth: :pluck, base_note: :c5, base_amp: 2)
  #sleep 1
end

live_loop :basistul do
  # ixi_techno, bitcrusher, compressor, flanger
  with_fx :ixi_techno, phase: 1 do
    # saw, supersaw, tb303, chipnoise | c2 | 0.5
    bas(use_synth: :saw, base_note: :c2, amp: 1)
  end
  sync "/live_loop/sega"
end

live_loop :tobosarul do
  # :bd_ada, :bd_tek, :bd_808, :bd_haus
  # :tabla_tas2, :tabla_ghe4, :tabla_dhec
  # :elec_plip, :elec_twip, :elec_pop
  # :drum_cymbal_closed#
  #if one_in(2)
  #toba(use_sample_1: :elec_pop, use_sample_2: :elec_twip, base_amp: 2, accent: [1,3].sample)
  #  else
  toba(use_sample_1: :tabla_dhec, use_sample_2: :bd_tek, base_amp: 1, accent: [2,3].sample)
  #  end
  
  sync "/live_loop/sega"
end

live_loop :romica do
  ah_ce_dor(base_amp=0.7, phase=16)
  sync "/live_loop/sega"
end
