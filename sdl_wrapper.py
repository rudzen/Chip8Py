from dataclasses import dataclass
from typing import Optional

import sdl2
import sdl2.ext
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

@dataclass
class SdlContext:
    """SDL context wrapper for CHIP-8 emulator"""
    window: Optional[sdl2.SDL_Window] = None
    renderer: Optional[sdl2.SDL_Renderer] = None
    texture: Optional[sdl2.SDL_Texture] = None
    window_width: int = 640
    window_height: int = 320
    chip8_width: int = 64
    chip8_height: int = 32
    error_state: StateError = StateError.NONE

    def __post_init__(self):
        """Initialize SDL after dataclass creation"""
        self.init_sdl()

    def init_sdl(self) -> StateError:
        """Initialize SDL components"""
        # Initialize SDL
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO | sdl2.SDL_INIT_AUDIO) != 0:
            self.error_state |= StateError.SDL_INIT
            return self.error_state

        # Create window
        self.window = sdl2.SDL_CreateWindow(
            b"CHIP-8 Emulator [Python + SDL2]",
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

        return StateError.NONE

    def cleanup(self):
        """Clean up SDL resources"""
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
            sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
            sdl2.SDL_RenderClear(self.renderer)

    @staticmethod
    def gfx_to_pixels(gfx_buffer):
        """Convert CHIP-8 graphics buffer to RGBA pixel data"""
        # Convert to numpy array
        arr = np.array(gfx_buffer, dtype=np.uint32)

        # Create RGBA pixels: white (255,255,255,255) for non-zero, black (0,0,0,0) for zero
        # We need 4 bytes per pixel (RGBA)
        pixels = np.zeros((len(gfx_buffer), 4), dtype=np.uint8)

        # Set RGB channels to 255 for non-zero pixels, alpha always 255
        mask = arr != 0
        pixels[mask] = [255, 255, 255, 255]  # White pixels
        pixels[~mask] = [0, 0, 0, 0]         # Black pixels (with alpha=255)

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
