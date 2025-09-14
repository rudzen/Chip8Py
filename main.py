import os
import sys
import time
from typing import List

import sdl2

from chip8 import Chip8
from common import StateError
from cpu import Cpu
from sdl_wrapper import SdlContext, map_sdl_key_to_chip8


def load_rom(file_path: str) -> List[int]:
    """Load ROM file and return as list of bytes"""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ROM file not found: {file_path}")

        with open(file_path, 'rb') as f:
            rom_data = f.read()

        return list(rom_data)
    except Exception as e:
        print(f"Error loading ROM: {e}")
        return []


def main():
    """Main entry point for CHIP-8 emulator"""
    # Check command line arguments
    test_mode = False
    rom_path = None

    if len(sys.argv) < 2:
        print("Usage: python main.py [-test] <rom_file>")
        sys.exit(1)

    # Parse command line arguments
    args = sys.argv[1:]
    if "-test" in args:
        test_mode = True
        args.remove("-test")

    if len(args) != 1:
        print("Usage: python main.py [-test] <rom_file>")
        sys.exit(1)

    rom_path = args[0]

    # Load ROM
    print(f"Loading ROM: {rom_path}")
    rom_data = load_rom(rom_path)
    if not rom_data:
        print("Failed to load ROM file")
        if test_mode:
            print(f"Test mode - Final StateError: {StateError.FILE_LOAD}")
        sys.exit(1)

    print(f"ROM loaded successfully, size: {len(rom_data)} bytes")

    # Initialize SDL
    sdl_context = SdlContext()

    # Check for test mode - exit after initialization
    if test_mode:
        print(f"Test mode - SDL initialization complete")
        print(f"Final StateError: {sdl_context.error_state}")
        if sdl_context.error_state == StateError.NONE:
            print("✅ All systems initialized successfully!")
        else:
            print("❌ Initialization failed with errors:")
            if sdl_context.error_state & StateError.SDL_INIT:
                print("  - SDL initialization failed")
            if sdl_context.error_state & StateError.WINDOW_CREATE:
                print("  - Window creation failed")
            if sdl_context.error_state & StateError.RENDERER_CREATE:
                print("  - Renderer creation failed")
            if sdl_context.error_state & StateError.AUDIO_INIT:
                print("  - Audio initialization failed")

        # Clean up and exit
        sdl_context.cleanup()
        sys.exit(0 if sdl_context.error_state == StateError.NONE else 1)

    # Normal operation continues here
    if sdl_context.error_state != StateError.NONE:
        print(f"SDL initialization failed with error: {sdl_context.error_state}")
        sys.exit(1)

    print("SDL initialized successfully")

    # Initialize CHIP-8 system
    chip8 = Chip8()

    # Load program into CHIP-8 memory
    Cpu.load_program(chip8, rom_data)
    print("ROM loaded into CHIP-8 memory")

    # Timing variables for 60Hz operation
    target_fps = 60
    frame_time = 1.0 / target_fps
    last_time = time.time()

    # Main emulation loop
    running = True
    print("Starting CHIP-8 emulator...")

    try:
        while running:
            current_time = time.time()

            # Handle SDL events
            event = sdl2.SDL_Event()
            while sdl2.SDL_PollEvent(event):
                if event.type == sdl2.SDL_QUIT:
                    running = False

                elif event.type == sdl2.SDL_KEYDOWN:
                    chip8_key = map_sdl_key_to_chip8(event.key.keysym.sym)
                    if chip8_key is not None:
                        # Set key as pressed in keyboard state
                        chip8.keyboard |= (1 << chip8_key)

                        # Handle waiting for key press
                        if chip8.waiting_for_key_press:
                            Cpu.key_pressed(chip8, chip8_key)

                elif event.type == sdl2.SDL_KEYUP:
                    chip8_key = map_sdl_key_to_chip8(event.key.keysym.sym)
                    if chip8_key is not None:
                        # Clear key from keyboard state
                        chip8.keyboard &= ~(1 << chip8_key)

                    # ESC key to quit
                    if event.key.keysym.sym == sdl2.SDLK_ESCAPE:
                        running = False

            # Execute CPU step if not waiting for key press
            if not chip8.waiting_for_key_press:
                try:
                    Cpu.step(chip8, 60)  # 60Hz timing
                except Exception as e:
                    print(f"CPU step error: {e}")
                    # Continue execution for now, could add error handling here

            # Handle audio based on sound timer
            if chip8.sound_timer > 0:
                sdl_context.start_beep()
            else:
                sdl_context.stop_beep()

            # Render at 60Hz
            if current_time - last_time >= frame_time:
                sdl_context.render_display(chip8.gfx)
                last_time = current_time

            # Small delay to prevent 100% CPU usage
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("\nEmulator interrupted by user")

    finally:
        print("Cleaning up...")
        sdl_context.cleanup()
        print("CHIP-8 emulator shutdown complete")


# python main.py your_rom_file.ch8

if __name__ == '__main__':
    main()
