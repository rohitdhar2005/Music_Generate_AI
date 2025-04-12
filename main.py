import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
import pygame
import threading
import os
import time
import random
from PIL import Image, ImageTk

# Initialize pygame mixer for audio playback
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

class AIModel:
    """Simple AI music generation model using algorithmic composition."""
    
    def __init__(self):
        # Define scales
        self.scales = {
            "Major": [0, 2, 4, 5, 7, 9, 11],
            "Minor": [0, 2, 3, 5, 7, 8, 10],
            "Pentatonic": [0, 2, 4, 7, 9],
            "Blues": [0, 3, 5, 6, 7, 10],
            "Chromatic": list(range(12))
        }
        
        # Define base frequencies for notes (C4 = 261.63 Hz)
        self.base_freq = 261.63
        
    def generate_melody(self, root_note=0, scale_type="Major", num_notes=16, 
                        tempo=120, complexity=0.5, octave=4, pattern_type="random"):
        """Generate a melody based on the given parameters."""
        scale = self.scales[scale_type]
        notes = []
        durations = []
        
        if pattern_type == "random":
            # Generate random notes from the scale
            for _ in range(num_notes):
                scale_index = random.randint(0, len(scale)-1)
                octave_shift = random.randint(-1, 1) if complexity > 0.6 else 0
                note_index = scale[scale_index]
                note = root_note + note_index + (octave + octave_shift) * 12
                notes.append(note)
                
                # Duration based on complexity (higher complexity = more varied rhythms)
                if complexity < 0.4:
                    durations.append(0.5)  # Simple rhythm
                else:
                    options = [0.25, 0.5, 1] if complexity < 0.7 else [0.25, 0.5, 0.75, 1]
                    durations.append(random.choice(options))
                
        elif pattern_type == "ascending":
            # Generate ascending pattern
            for i in range(num_notes):
                idx = i % len(scale)
                octave_shift = i // len(scale)
                note = root_note + scale[idx] + (octave + octave_shift) * 12
                notes.append(note)
                durations.append(0.5)
                
        elif pattern_type == "descending":
            # Generate descending pattern
            for i in range(num_notes):
                idx = (len(scale) - 1) - (i % len(scale))
                octave_shift = -(i // len(scale))
                note = root_note + scale[idx] + (octave + octave_shift) * 12
                notes.append(note)
                durations.append(0.5)
                
        elif pattern_type == "arpeggios":
            # Generate arpeggios (focus on 1st, 3rd, 5th notes of scale)
            arp_indices = [0, 2, 4] if len(scale) >= 5 else [0, 2, len(scale)-1]
            for i in range(num_notes):
                idx = arp_indices[i % len(arp_indices)]
                octave_shift = i // len(arp_indices) if i // len(arp_indices) < 2 else 0
                note = root_note + scale[idx] + (octave + octave_shift) * 12
                notes.append(note)
                durations.append(random.choice([0.25, 0.5]))
        
        # Calculate actual durations in seconds based on tempo
        seconds_per_beat = 60 / tempo
        durations_seconds = [d * seconds_per_beat for d in durations]
        
        return notes, durations_seconds
    
    def generate_chord_progression(self, root_note=0, scale_type="Major", num_chords=4):
        """Generate a basic chord progression."""
        scale = self.scales[scale_type]
        
        # Common chord progressions by scale degree
        progressions = {
            "Major": [[0, 5, 3, 4], [0, 3, 4, 0], [0, 4, 5, 3], [0, 5, 1, 4]],
            "Minor": [[0, 5, 3, 4], [0, 6, 2, 5], [0, 3, 4, 0], [0, 7, 3, 4]]
        }
        
        # Default to major progressions if scale not found
        prog_options = progressions.get(scale_type, progressions["Major"])
        progression = random.choice(prog_options)[:num_chords]
        
        chords = []
        for degree in progression:
            # Create triad: root, third, fifth
            if degree < len(scale):
                chord_root = scale[degree]
                chord_third_idx = (degree + 2) % len(scale)
                chord_fifth_idx = (degree + 4) % len(scale)
                
                chord_third = scale[chord_third_idx]
                chord_fifth = scale[chord_fifth_idx]
                
                # Adjust third and fifth if they're lower than the root (wrap around)
                if chord_third < chord_root:
                    chord_third += 12
                if chord_fifth < chord_root:
                    chord_fifth += 12
                
                # Add octave offset and root note
                chord = [
                    root_note + chord_root + 4 * 12, 
                    root_note + chord_third + 4 * 12, 
                    root_note + chord_fifth + 4 * 12
                ]
                chords.append(chord)
        
        return chords
    
    def note_to_freq(self, note):
        """Convert note number to frequency (A4 = 69)."""
        return self.base_freq * (2 ** ((note - 60) / 12))
    
    def generate_sample(self, note, duration, amplitude=0.5, sample_rate=44100):
        """Generate an audio sample for a note."""
        # Simple sine wave synthesis
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        freq = self.note_to_freq(note)
        
        # Basic ADSR envelope
        attack = int(0.05 * sample_rate)
        decay = int(0.1 * sample_rate)
        release = int(0.2 * sample_rate)
        
        env = np.ones(len(t))
        if attack > 0:
            env[:attack] = np.linspace(0, 1, attack)
        if decay > 0 and len(t) > attack:
            decay_end = min(attack + decay, len(t))
            env[attack:decay_end] = np.linspace(1, 0.8, decay_end - attack)
        if release > 0 and len(t) > release:
            env[-release:] = np.linspace(env[-release] if len(t) > release else 0.8, 0, release)
        
        # Generate waveform with envelope
        sine = np.sin(2 * np.pi * freq * t)
        return (sine * env * amplitude).astype(np.float32)
    
    def generate_audio(self, notes, durations, chord_progression=None, chord_duration=2.0, sample_rate=44100):
        """Generate complete audio sample from melody and optional chord progression."""
        total_samples = int(sum(durations) * sample_rate)
        audio_data = np.zeros(total_samples, dtype=np.float32)
        
        # Generate melody
        current_sample = 0
        for note, duration in zip(notes, durations):
            samples = int(duration * sample_rate)
            note_data = self.generate_sample(note, duration, 0.4, sample_rate)
            
            # Pad or truncate as needed
            if len(note_data) > samples:
                note_data = note_data[:samples]
            elif len(note_data) < samples:
                note_data = np.pad(note_data, (0, samples - len(note_data)))
            
            # Add to audio data
            end_sample = current_sample + samples
            if end_sample <= total_samples:
                audio_data[current_sample:end_sample] += note_data
            else:
                audio_data[current_sample:] += note_data[:total_samples-current_sample]
            
            current_sample += samples
        
        # Add chord progression if provided
        if chord_progression:
            chord_samples = int(chord_duration * sample_rate)
            chord_pos = 0
            
            for chord in chord_progression:
                chord_audio = np.zeros(chord_samples, dtype=np.float32)
                
                # Mix chord notes
                for note in chord:
                    note_data = self.generate_sample(note, chord_duration, 0.15, sample_rate)
                    if len(note_data) < chord_samples:
                        note_data = np.pad(note_data, (0, chord_samples - len(note_data)))
                    else:
                        note_data = note_data[:chord_samples]
                    chord_audio += note_data
                
                # Add chord to the main audio
                end_pos = chord_pos + chord_samples
                if end_pos <= total_samples:
                    audio_data[chord_pos:end_pos] += chord_audio
                else:
                    audio_data[chord_pos:] += chord_audio[:total_samples-chord_pos]
                    break
                
                chord_pos += chord_samples
                if chord_pos >= total_samples:
                    break
        
        # Normalize audio to prevent clipping
        max_amplitude = np.max(np.abs(audio_data))
        if max_amplitude > 1.0:
            audio_data = audio_data / max_amplitude * 0.9
        
        # Convert to 16-bit PCM
        audio_data_16bit = (audio_data * 32767).astype(np.int16)
        
        return audio_data_16bit

class MusicGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Music Generator")
        self.root.geometry("900x650")
        self.root.resizable(False, False)
        self.root.configure(bg="#2E2E2E")
        
        # Set app icon
        # self.root.iconbitmap("music_icon.ico") # Add your own icon file
        
        # Initialize AI model
        self.ai_model = AIModel()
        
        # Initialize audio playback variables
        self.is_playing = False
        self.current_audio = None
        self.play_thread = None
        
        # Note names for display
        self.note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        
        # Create the GUI
        self.setup_ui()
        
        # Display visualizer canvas
        self.setup_visualizer()
    
    def setup_ui(self):
        """Set up the user interface."""
        # Main frame
        main_frame = tk.Frame(self.root, bg="#2E2E2E")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(main_frame, text="AI Music Generator", 
                              font=("Helvetica", 24, "bold"), 
                              fg="#E0E0E0", bg="#2E2E2E")
        title_label.pack(pady=10)
        
        # Content frame with two columns
        content_frame = tk.Frame(main_frame, bg="#2E2E2E")
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left column - Controls
        controls_frame = tk.Frame(content_frame, bg="#3D3D3D", padx=15, pady=15, bd=0, 
                                 highlightbackground="#555", highlightthickness=1)
        controls_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        # Right column - Visualizer and Buttons
        right_frame = tk.Frame(content_frame, bg="#2E2E2E")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Style for ttk widgets
        self.style = ttk.Style()
        self.style.theme_use('alt')  # Use 'alt' theme as base
        self.style.configure("TCombobox", fieldbackground="#4A4A4A", background="#4A4A4A", 
                           foreground="#E0E0E0", selectbackground="#6A6A6A", padding=5)
        self.style.configure("TScale", background="#3D3D3D", troughcolor="#4A4A4A")
        self.style.map('TCombobox', fieldbackground=[('readonly', '#4A4A4A')])
        self.style.map('TScale', background=[('active', '#5A5A5A')])
        
        # --- Controls Frame Content ---
        controls_title = tk.Label(controls_frame, text="Music Parameters", 
                                 font=("Helvetica", 14, "bold"), fg="#E0E0E0", bg="#3D3D3D")
        controls_title.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=tk.W)
        
        # Root Note
        tk.Label(controls_frame, text="Root Note:", fg="#E0E0E0", bg="#3D3D3D").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.root_note_var = tk.StringVar(value="C")
        root_note_combo = ttk.Combobox(controls_frame, textvariable=self.root_note_var, values=self.note_names,
                                     state="readonly", width=10)
        root_note_combo.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Scale Type
        tk.Label(controls_frame, text="Scale:", fg="#E0E0E0", bg="#3D3D3D").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.scale_var = tk.StringVar(value="Major")
        scale_combo = ttk.Combobox(controls_frame, textvariable=self.scale_var, 
                                  values=list(self.ai_model.scales.keys()),
                                  state="readonly", width=10)
        scale_combo.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Pattern Type
        tk.Label(controls_frame, text="Pattern:", fg="#E0E0E0", bg="#3D3D3D").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.pattern_var = tk.StringVar(value="random")
        pattern_combo = ttk.Combobox(controls_frame, textvariable=self.pattern_var, 
                                    values=["random", "ascending", "descending", "arpeggios"],
                                    state="readonly", width=10)
        pattern_combo.grid(row=3, column=1, sticky=tk.W, pady=5)
        
        # Octave
        tk.Label(controls_frame, text="Octave:", fg="#E0E0E0", bg="#3D3D3D").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.octave_var = tk.IntVar(value=4)
        octave_frame = tk.Frame(controls_frame, bg="#3D3D3D")
        octave_frame.grid(row=4, column=1, sticky=tk.W, pady=5)
        
        ttk.Button(octave_frame, text="-", width=2, 
                 command=lambda: self.octave_var.set(max(2, self.octave_var.get()-1))).pack(side=tk.LEFT)
        tk.Label(octave_frame, textvariable=self.octave_var, width=2, 
               fg="#E0E0E0", bg="#4A4A4A", padx=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(octave_frame, text="+", width=2, 
                 command=lambda: self.octave_var.set(min(6, self.octave_var.get()+1))).pack(side=tk.LEFT)
        
        # Tempo
        tk.Label(controls_frame, text="Tempo:", fg="#E0E0E0", bg="#3D3D3D").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.tempo_var = tk.IntVar(value=120)
        tempo_scale = ttk.Scale(controls_frame, from_=60, to=180, variable=self.tempo_var, 
                              orient=tk.HORIZONTAL, length=150)
        tempo_scale.grid(row=5, column=1, sticky=tk.W, pady=5)
        tk.Label(controls_frame, textvariable=self.tempo_var, 
               fg="#E0E0E0", bg="#4A4A4A", width=3, padx=5).grid(row=5, column=2, sticky=tk.W)
        
        # Complexity
        tk.Label(controls_frame, text="Complexity:", fg="#E0E0E0", bg="#3D3D3D").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.complexity_var = tk.DoubleVar(value=0.5)
        complexity_scale = ttk.Scale(controls_frame, from_=0.0, to=1.0, variable=self.complexity_var, 
                                   orient=tk.HORIZONTAL, length=150)
        complexity_scale.grid(row=6, column=1, sticky=tk.W, pady=5)
        
        # Display formatted complexity
        self.complexity_label_var = tk.StringVar()
        self.update_complexity_label()
        complexity_label = tk.Label(controls_frame, textvariable=self.complexity_label_var, 
                                   fg="#E0E0E0", bg="#4A4A4A", width=3, padx=5)
        complexity_label.grid(row=6, column=2, sticky=tk.W)
        complexity_scale.bind("<Motion>", lambda e: self.update_complexity_label())
        
        # Number of Notes
        tk.Label(controls_frame, text="# of Notes:", fg="#E0E0E0", bg="#3D3D3D").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.num_notes_var = tk.IntVar(value=16)
        notes_scale = ttk.Scale(controls_frame, from_=4, to=32, variable=self.num_notes_var, 
                              orient=tk.HORIZONTAL, length=150)
        notes_scale.grid(row=7, column=1, sticky=tk.W, pady=5)
        tk.Label(controls_frame, textvariable=self.num_notes_var, 
               fg="#E0E0E0", bg="#4A4A4A", width=3, padx=5).grid(row=7, column=2, sticky=tk.W)
        
        # Use Chords
        tk.Label(controls_frame, text="Add Chords:", fg="#E0E0E0", bg="#3D3D3D").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.use_chords_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(controls_frame, variable=self.use_chords_var).grid(row=8, column=1, sticky=tk.W, pady=5)
        
        # Number of Chords
        tk.Label(controls_frame, text="# of Chords:", fg="#E0E0E0", bg="#3D3D3D").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.num_chords_var = tk.IntVar(value=4)
        chords_frame = tk.Frame(controls_frame, bg="#3D3D3D")
        chords_frame.grid(row=9, column=1, sticky=tk.W, pady=5)
        
        ttk.Button(chords_frame, text="-", width=2, 
                 command=lambda: self.num_chords_var.set(max(2, self.num_chords_var.get()-1))).pack(side=tk.LEFT)
        tk.Label(chords_frame, textvariable=self.num_chords_var, width=2, 
               fg="#E0E0E0", bg="#4A4A4A", padx=10).pack(side=tk.LEFT, padx=5)
        ttk.Button(chords_frame, text="+", width=2, 
                 command=lambda: self.num_chords_var.set(min(8, self.num_chords_var.get()+1))).pack(side=tk.LEFT)
        
        # --- Buttons Frame in Right Column ---
        buttons_frame = tk.Frame(right_frame, bg="#2E2E2E", pady=10)
        buttons_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Generate button
        generate_btn = tk.Button(buttons_frame, text="Generate Music", bg="#4CAF50", fg="white", 
                               font=("Helvetica", 12, "bold"), padx=15, pady=8,
                               command=self.generate_music)
        generate_btn.pack(side=tk.LEFT, padx=5)
        
        # Play/Pause button
        self.play_btn_text = tk.StringVar(value="Play")
        self.play_btn = tk.Button(buttons_frame, textvariable=self.play_btn_text, bg="#2196F3", fg="white",
                                font=("Helvetica", 12, "bold"), padx=15, pady=8,
                                command=self.toggle_playback, state=tk.DISABLED)
        self.play_btn.pack(side=tk.LEFT, padx=5)
        
        # Save button
        save_btn = tk.Button(buttons_frame, text="Save", bg="#FF9800", fg="white",
                           font=("Helvetica", 12, "bold"), padx=15, pady=8,
                           command=self.save_audio, state=tk.DISABLED)
        save_btn.pack(side=tk.LEFT, padx=5)
        self.save_btn = save_btn
        
        # Status label
        self.status_var = tk.StringVar(value="Ready to generate music")
        status_label = tk.Label(right_frame, textvariable=self.status_var, 
                              fg="#E0E0E0", bg="#2E2E2E", pady=5)
        status_label.pack(side=tk.BOTTOM, fill=tk.X)
    
    def update_complexity_label(self):
        """Update the displayed complexity value."""
        value = self.complexity_var.get()
        self.complexity_label_var.set(f"{value:.1f}")
    
    def setup_visualizer(self):
        """Set up the audio visualizer."""
        visualizer_frame = tk.Frame(self.root.winfo_children()[0].winfo_children()[1], 
                                   bg="#1E1E1E", bd=0, highlightbackground="#555", highlightthickness=1)
        visualizer_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.canvas = tk.Canvas(visualizer_frame, bg="#1E1E1E", bd=0, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initialize visualization data
        self.visualizer_data = []
        self.is_visualizing = False
        
        # Draw initial visualization
        self.draw_empty_visualizer()
    
    def draw_empty_visualizer(self):
        """Draw the empty visualizer."""
        self.canvas.delete("all")
        width = self.canvas.winfo_width() or 400
        height = self.canvas.winfo_height() or 200
        
        # Draw piano keyboard at bottom
        key_width = width / 52
        white_key_height = height / 4
        
        # Draw center line
        self.canvas.create_line(0, height/2, width, height/2, fill="#333333", dash=(4, 4))
        
        # Add message
        self.canvas.create_text(width/2, height/2 - 30, 
                              text="Generate music to see visualization", 
                              fill="#666666", font=("Helvetica", 12))
    
    def generate_music(self):
        """Generate music based on current parameters."""
        # Update status
        self.status_var.set("Generating music...")
        self.root.update()
        
        try:
            # Get parameters
            root_note_idx = self.note_names.index(self.root_note_var.get())
            scale_type = self.scale_var.get()
            num_notes = self.num_notes_var.get()
            tempo = self.tempo_var.get()
            complexity = self.complexity_var.get()
            octave = self.octave_var.get()
            pattern_type = self.pattern_var.get()
            use_chords = self.use_chords_var.get()
            num_chords = self.num_chords_var.get()
            
            # Generate melody
            notes, durations = self.ai_model.generate_melody(
                root_note=root_note_idx, 
                scale_type=scale_type,
                num_notes=num_notes,
                tempo=tempo,
                complexity=complexity,
                octave=octave,
                pattern_type=pattern_type
            )
            
            # Generate chord progression if needed
            chord_progression = None
            if use_chords:
                chord_progression = self.ai_model.generate_chord_progression(
                    root_note=root_note_idx,
                    scale_type=scale_type,
                    num_chords=num_chords
                )
            
            # Generate audio data
            audio_data = self.ai_model.generate_audio(
                notes=notes,
                durations=durations,
                chord_progression=chord_progression,
                chord_duration=sum(durations)/num_chords if use_chords else 0
            )
            
            # Save audio data and visualization data
            self.current_audio = audio_data
            self.visualizer_data = list(zip(notes, durations))
            
            # Enable playback controls
            self.play_btn.config(state=tk.NORMAL)
            self.save_btn.config(state=tk.NORMAL)
            
            # Update visualizer
            self.draw_visualization(notes, durations)
            
            # Update status
            self.status_var.set("Music generated successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while generating music: {str(e)}")
            self.status_var.set("Error generating music.")
    
    def draw_visualization(self, notes, durations):
        """Draw the melody visualization."""
        self.canvas.delete("all")
        
        width = self.canvas.winfo_width() or 400
        height = self.canvas.winfo_height() or 200
        
        # Calculate total duration
        total_duration = sum(durations)
        
        # Draw time grid
        grid_color = "#333333"
        for i in range(1, 10):
            x = width * (i / 10)
            self.canvas.create_line(x, 0, x, height, fill=grid_color, dash=(2, 4))
        
        # Draw horizontal center line
        self.canvas.create_line(0, height/2, width, height/2, fill="#444444", width=1)
        
        # Draw note blocks
        current_x = 0
        min_note = min(notes)
        max_note = max(notes)
        note_range = max(max_note - min_note, 12)
        
        for note, duration in zip(notes, durations):
            # Calculate position
            x1 = width * (current_x / total_duration)
            current_x += duration
            x2 = width * (current_x / total_duration)
            
            # Map note to y position (higher notes at top)
            relative_note = 1 - ((note - min_note) / note_range)
            y_center = height * (0.2 + relative_note * 0.6)
            block_height = height / 20
            
            # Calculate color based on note (hue)
            hue = (note % 12) / 12
            saturation = 0.7 + (duration / max(durations)) * 0.3
            brightness = 0.6 + (note / 127) * 0.4
            
            # Convert HSV to RGB hex
            r, g, b = self.hsv_to_rgb(hue, saturation, brightness)
            color = f"#{r:02x}{g:02x}{b:02x}"
            
            # Draw rounded rectangle for note
            self.canvas.create_rectangle(
                x1, y_center - block_height/2, 
                x2 - 1, y_center + block_height/2, 
                fill=color, outline="#000000", width=1
            )
        
        # Draw piano keyboard at the bottom of the visualization
        self.draw_piano_keyboard(height * 0.85, height * 0.15, width)
    
    def draw_piano_keyboard(self, y_start, height, width):
        """Draw a simple piano keyboard at the bottom of the visualization."""
        # Draw keyboard (one octave)
        white_keys = [0, 2, 4, 5, 7, 9, 11]  # C, D, E, F, G, A, B
        black_keys = [1, 3, 6, 8, 10]  # C#, D#, F#, G#, A#
        
        # Calculate key dimensions
        num_octaves = 2
        white_key_width = width / (7 * num_octaves)
        black_key_width = white_key_width * 0.6
        
        # Draw white keys
        for octave in range(num_octaves):
            for i, note in enumerate(white_keys):
                x1 = octave * 7 * white_key_width + i * white_key_width
                x2 = x1 + white_key_width
                
                self.canvas.create_rectangle(
                    x1, y_start, x2, y_start + height,
                    fill="#FFFFFF", outline="#888888", width=1
                )
        
        # Draw black keys
        for octave in range(num_octaves):
            for i, note in enumerate(black_keys):
                # Convert black key index to position relative to white keys
                if i < 2:  # C#, D#
                    pos = i + 0.75
                else:  # F#, G#, A#
                    pos = i + 1.75
                
                x_center = octave * 7 * white_key_width + pos * white_key_width
                x1 = x_center - black_key_width/2
                x2 = x_center + black_key_width/2
                
                self.canvas.create_rectangle(
                    x1, y_start, x2, y_start + height * 0.6,
                    fill="#000000", outline="#888888", width=1
                )
    
    def hsv_to_rgb(self, h, s, v):
        """Convert HSV color to RGB."""
        if s == 0.0:
            return (int(v * 255), int(v * 255), int(v * 255))
        
        h = h * 6.0
        i = int(h)
        f = h - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))
        
        if i == 0:
            return (int(v * 255), int(t * 255), int(p * 255))
        elif i == 1:
            return (int(q * 255), int(v * 255), int(p * 255))
        elif i == 2:
            return (int(p * 255), int(v * 255), int(t * 255))
        elif i == 3:
            return (int(p * 255), int(q * 255), int(v * 255))
        elif i == 4:
            return (int(t * 255), int(p * 255), int(v * 255))
        else:
            return (int(v * 255), int(p * 255), int(q * 255))
    
    def toggle_playback(self):
        """Toggle between play and pause."""
        if not self.is_playing:
            # Start playback
            self.is_playing = True
            self.play_btn_text.set("Pause")
            
            # Start playback in separate thread
            self.play_thread = threading.Thread(target=self.play_audio)
            self.play_thread.daemon = True
            self.play_thread.start()
            
            # Start visualization
            self.is_visualizing = True
            self.update_playback_visualization()
        else:
            # Stop playback
            self.is_playing = False
            self.play_btn_text.set("Play")
            pygame.mixer.music.stop()
    
    def play_audio(self):
        """Play the generated audio."""
        if self.current_audio is None:
            return
        
        try:
            # Convert to temporary WAV file for pygame to play
            temp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_music.wav")
            
            # Save audio to temp file using scipy
            from scipy.io import wavfile
            wavfile.write(temp_file, 44100, self.current_audio)
            
            # Load and play the audio
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            
            # Wait for music to finish or be stopped
            while pygame.mixer.music.get_busy() and self.is_playing:
                time.sleep(0.1)
            
            # Clean up
            self.is_playing = False
            self.root.after(0, lambda: self.play_btn_text.set("Play"))
            
            # Remove temp file
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
                
        except Exception as e:
            messagebox.showerror("Playback Error", f"Error playing audio: {str(e)}")
            self.is_playing = False
            self.root.after(0, lambda: self.play_btn_text.set("Play"))
    
    def update_playback_visualization(self):
        """Update visualization during playback."""
        if not self.is_playing or not self.is_visualizing:
            return
        
        # Check if music is still playing
        if not pygame.mixer.music.get_busy():
            self.is_visualizing = False
            return
        
        # Get current playback position
        pos = pygame.mixer.music.get_pos() / 1000.0  # Convert to seconds
        
        # Highlight current position in visualization
        self.highlight_playback_position(pos)
        
        # Schedule next update
        self.root.after(50, self.update_playback_visualization)
    
    def highlight_playback_position(self, pos):
        """Highlight the current playback position on the visualizer."""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        
        # Delete previous position line
        self.canvas.delete("playback_pos")
        
        # Calculate total duration
        total_duration = sum(d for _, d in self.visualizer_data)
        
        # Determine x position
        x_pos = (pos / total_duration) * width
        if x_pos > width:
            x_pos = width
        
        # Draw position line
        self.canvas.create_line(
            x_pos, 0, x_pos, height,
            fill="#FFFF00", width=2, tags="playback_pos"
        )
    
    def save_audio(self):
        """Save the generated audio to a WAV file."""
        if self.current_audio is None:
            messagebox.showinfo("Save", "No audio to save. Generate music first.")
            return
        
        try:
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav"), ("All files", "*.*")],
                title="Save Audio As"
            )
            
            if not file_path:
                return  # User cancelled
            
            # Save audio using scipy
            from scipy.io import wavfile
            wavfile.write(file_path, 44100, self.current_audio)
            
            self.status_var.set(f"Saved audio to {os.path.basename(file_path)}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving audio: {str(e)}")
            self.status_var.set("Error saving audio.")

if __name__ == "__main__":
    # Initialize pygame
    pygame.init()
    
    # Create main window
    root = tk.Tk()
    app = MusicGenerator(root)
    
    # Start main loop
    root.mainloop()
    
    # Clean up
    pygame.quit() 
