from dataclasses import dataclass
from typing import Optional
import ctypes

import sdl2
import sdl2.ext
import sdl2.sdlmixer
import numpy as np

from common import StateError


def map_sdl_key_to_chip8(sdl_key) -> Optional[int]:
    """Map SDL key codes to CHIP-8 hex keypad (0-F)"""
    key_map = {
        sdl2.SDLK_1: 0x1, sdl2.SDLK_2: 0x2, sdl2.SDLK_3: 0x3, sdl2.SDLK_4: 0xC,
        sdl2.SDLK_q: 0x4, sdl2.SDLK_w: 0x5, sdl2.SDLK_e: 0x6, sdl2.SDLK_r: 0xD,
        sdl2.SDLK_a: 0x7, sdl2.SDLK_s: 0x8, sdl2.SDLK_d: 0x9, sdl2.SDLK_f: 0xE,
        sdl2.SDLK_z: 0xA, sdl2.SDLK_x: 0x0, sdl2.SDLK_c: 0xB, sdl2.SDLK_v: 0xF
    }
    return key_map.get(sdl_key)


class AudioGenerator:
    """Generate square wave audio for CHIP-8 beep sound"""

    def __init__(self, sample_rate=44100, frequency=440, amplitude=0.1):
        self.sample_rate = sample_rate
        self.frequency = frequency
        self.amplitude = amplitude
        self.phase = 0.0
        self.phase_increment = 2.0 * np.pi * frequency / sample_rate

    def generate_square_wave(self, num_samples):
        """Generate square wave audio samples"""
        samples = []
        for _ in range(num_samples):
            # Generate square wave
            sample = self.amplitude if np.sin(self.phase) >= 0 else -self.amplitude
            samples.append(int(sample * 32767))  # Convert to 16-bit signed integer
            self.phase += self.phase_increment
            if self.phase >= 2.0 * np.pi:
                self.phase -= 2.0 * np.pi
        return samples


@dataclass
class SdlContext:
    """SDL context wrapper for CHIP-8 emulator with audio support"""
    window: Optional[sdl2.SDL_Window] = None
    renderer: Optional[sdl2.SDL_Renderer] = None
    texture: Optional[sdl2.SDL_Texture] = None
    audio_device: Optional[int] = None
    audio_spec: Optional[sdl2.SDL_AudioSpec] = None
    window_width: int = 640
    window_height: int = 320
    chip8_width: int = 64
    chip8_height: int = 32
    error_state: StateError = StateError.NONE
    audio_generator: Optional[AudioGenerator] = None
    beep_playing: bool = False

    def __post_init__(self):
        """Initialize SDL after dataclass creation"""
        self.init_sdl()

    def audio_callback(self, userdata, stream, length):
        """Audio callback function for generating beep sound"""
        if not self.beep_playing or not self.audio_generator:
            # Fill with silence
            ctypes.memset(stream, 0, length)
            return

        # Generate audio samples
        num_samples = length // 2  # 16-bit samples
        samples = self.audio_generator.generate_square_wave(num_samples)

        # Convert to ctypes array and copy to stream
        sample_array = (ctypes.c_int16 * num_samples)(*samples)
        ctypes.memmove(stream, sample_array, length)

    def init_sdl(self) -> StateError:
        """Initialize SDL components including audio"""
        # Initialize SDL
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_AUDIO) != 0:
            self.error_state |= StateError.SDL_INIT
            return self.error_state

        # Create window
        self.window = sdl2.SDL_CreateWindow(
            b"CHIP-8 Emulator [Python + SDL2 + Audio]",
            sdl2.SDL_WINDOWPOS_CENTERED,
            sdl2.SDL_WINDOWPOS_CENTERED,
            self.window_width,
            self.window_height,
            sdl2.SDL_WINDOW_SHOWN
        )

        if not self.window:
            self.error_state |= StateError.WINDOW_CREATE
            return self.error_state

        # Create renderer
        self.renderer = sdl2.SDL_CreateRenderer(
            self.window,
            -1,
            sdl2.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC
        )

        if not self.renderer:
            self.error_state |= StateError.RENDERER_CREATE
            return self.error_state

        # Create texture for CHIP-8 display
        self.texture = sdl2.SDL_CreateTexture(
            self.renderer,
            sdl2.SDL_PIXELFORMAT_RGBA8888,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            self.chip8_width,
            self.chip8_height
        )

        if not self.texture:
            self.error_state |= StateError.RENDERER_CREATE
            return self.error_state

        # Initialize audio
        if not self.init_audio():
            self.error_state |= StateError.AUDIO_INIT
            return self.error_state

        return StateError.NONE

    def init_audio(self) -> bool:
        """Initialize SDL audio subsystem"""
        try:
            # Create audio generator
            self.audio_generator = AudioGenerator(frequency=440, amplitude=0.3)

            # Use a simpler approach without callback for now
            desired_spec = sdl2.SDL_AudioSpec(
                freq=44100,
                aformat=sdl2.AUDIO_S16SYS,
                channels=1,
                samples=1024
            )

            obtained_spec = sdl2.SDL_AudioSpec(
                freq=0,
                aformat=0,
                channels=0,
                samples=0
            )

            # Open audio device
            self.audio_device = sdl2.SDL_OpenAudioDevice(
                None,  # Device name (None for default)
                0,     # Not capture device
                desired_spec,
                obtained_spec,
                0      # No changes allowed
            )

            if self.audio_device == 0:
                print(f"Failed to open audio device: {sdl2.SDL_GetError().decode()}")
                return False

            self.audio_spec = obtained_spec
            print(f"Audio initialized: {obtained_spec.freq}Hz, {obtained_spec.channels} channel(s)")
            return True

        except Exception as e:
            print(f"Audio initialization error: {e}")
            return False

    def start_beep(self):
        """Start playing the beep sound"""
        if self.audio_device and not self.beep_playing:
            self.beep_playing = True
            # Generate some audio data and queue it
            self._queue_beep_audio()
            sdl2.SDL_PauseAudioDevice(self.audio_device, 0)  # Unpause

    def stop_beep(self):
        """Stop playing the beep sound"""
        if self.audio_device and self.beep_playing:
            self.beep_playing = False
            sdl2.SDL_PauseAudioDevice(self.audio_device, 1)  # Pause
            sdl2.SDL_ClearQueuedAudio(self.audio_device)  # Clear any queued audio

    def _queue_beep_audio(self):
        """Queue beep audio data"""
        if not self.audio_device or not self.audio_generator:
            return

        # Generate 1/10 second of audio (short beep bursts)
        samples_per_burst = self.audio_spec.freq // 10
        samples = self.audio_generator.generate_square_wave(samples_per_burst)

        # Convert to bytes
        sample_array = (ctypes.c_int16 * len(samples))(*samples)
        audio_data = ctypes.string_at(sample_array, len(samples) * 2)

        # Queue the audio
        sdl2.SDL_QueueAudio(self.audio_device, audio_data, len(audio_data))

    def cleanup(self):
        """Clean up SDL resources"""
        if self.audio_device:
            sdl2.SDL_CloseAudioDevice(self.audio_device)
        if self.texture:
            sdl2.SDL_DestroyTexture(self.texture)
        if self.renderer:
            sdl2.SDL_DestroyRenderer(self.renderer)
        if self.window:
            sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    def clear_screen(self):
        """Clear the screen to black"""
        if self.renderer:
            sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 0)
            sdl2.SDL_RenderClear(self.renderer)

    @staticmethod
    def gfx_to_pixels(gfx_buffer):
        """Convert CHIP-8 graphics buffer to RGBA pixel data"""
        # Convert to numpy array
        arr = np.array(gfx_buffer, dtype=np.uint32)

        # Create RGBA pixels: white (255,255,255,255) for non-zero, black (0,0,0,255) for zero
        # We need 4 bytes per pixel (RGBA)
        pixels = np.zeros((len(gfx_buffer), 4), dtype=np.uint8)

        # Set RGB channels to 255 for non-zero pixels, alpha always 255
        mask = arr != 0
        pixels[mask] = [255, 255, 255, 255]  # White pixels
        pixels[~mask] = [0, 0, 0, 0]         # Black pixels (alpha=255 for proper rendering)

        return pixels.flatten().tobytes()

    def render_display(self, gfx_buffer):
        """Render the CHIP-8 display buffer to screen"""
        if not self.renderer or not self.texture:
            return

        # Update texture with pixel data
        pitch = self.chip8_width * 4  # 4 bytes per pixel (RGBA)

        # Convert CHIP-8 graphics buffer to RGBA pixels
        pixel_data = self.gfx_to_pixels(gfx_buffer)

        sdl2.SDL_UpdateTexture(
            self.texture,
            None,
            pixel_data,
            pitch
        )

        # Clear and render
        self.clear_screen()
        sdl2.SDL_RenderCopy(self.renderer, self.texture, None, None)
        sdl2.SDL_RenderPresent(self.renderer)
