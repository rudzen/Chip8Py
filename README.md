# CHIP-8 Emulator

A CHIP-8 emulator written in Python using SDL2 for graphics and input handling. This emulator can run classic CHIP-8 games and programs with accurate timing and graphics rendering.

## Features

- **Full CHIP-8 instruction set implementation**
- **60Hz display refresh rate**
- **Accurate timing for delay and sound timers**
- **Keyboard input mapping** to CHIP-8 hex keypad
- **SDL2-based graphics rendering** with pixel-perfect scaling
- **Cross-platform compatibility** (Windows, Linux, macOS)
- **ROM loading from command line**
- **Real-time emulation** with proper frame timing

## Project Structure

```
chip8/
├── main.py           # Main entry point and emulation loop
├── chip8.py          # CHIP-8 system state dataclass
├── cpu.py            # CPU instruction processing and execution
├── sdl_wrapper.py    # SDL2 wrapper for graphics and input
├── common.py         # Common enums and utilities
├── roms/             # Directory for ROM files
│   └── sample.ch8    # Sample ROM file
└── README.md         # This file
```

## Dependencies

This project requires the following Python packages:

- **PySDL2** - Python bindings for SDL2
- **PySDL2-dll** - SDL2 binary libraries for Windows
- **numpy** - For optimized graphics buffer processing

## Installation

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd chip8
```

### 2. Install Dependencies

Install all required dependencies using pip:

```bash
pip install PySDL2 PySDL2-dll numpy
```

**OR** install them individually:

```bash
pip install PySDL2        # SDL2 Python bindings
pip install PySDL2-dll    # SDL2 binary libraries (Windows)
pip install numpy         # Numerical computing library
```

### 3. Verify Installation

Test that SDL2 is working properly:

```bash
python -c "import sdl2; print('SDL2 imported successfully')"
```

You should see: `SDL2 imported successfully` (with a possible warning about using SDL2 binaries, which is normal).

## Usage

### Basic Usage

Run the emulator with a ROM file:

```bash
python main.py <rom_file>
```

### Test Mode

Test system initialization without running the emulator:

```bash
python main.py -test <rom_file>
```

The `-test` parameter will:
- Load the specified ROM file
- Initialize all SDL systems (video, audio, window, renderer)
- Display detailed initialization status
- Exit immediately with success/failure report
- Clean up all resources properly

**Example test output:**
```
Loading ROM: .\roms\sample.ch8
ROM loaded successfully, size: 26 bytes
Audio initialized: 44100Hz, 1 channel(s)
Test mode - SDL initialization complete
Final StateError: StateError.NONE
✅ All systems initialized successfully!
```

If initialization fails, you'll see detailed error information:
```
❌ Initialization failed with errors:
  - SDL initialization failed
  - Audio initialization failed
```

### Example

```bash
python main.py roms/sample.ch8              # Run emulator
python main.py -test roms/sample.ch8        # Test initialization only
```

### Controls

The CHIP-8 system has a 16-key hexadecimal keypad (0-F) mapped to your keyboard as follows:

```
CHIP-8 Keypad    Keyboard
1 2 3 C          1 2 3 4
4 5 6 D          Q W E R  
7 8 9 E          A S D F
A 0 B F          Z X C V
```

**Additional Controls:**
- **ESC** - Exit emulator
- **Ctrl+C** - Force quit (in terminal)

### Finding ROMs

You can find CHIP-8 ROMs from various sources:
- [CHIP-8 Archive](https://www.chip-8.com/)
- [Awesome CHIP-8](https://github.com/tobiasvl/awesome-chip-8)
- Public domain games and demos

Popular games include:
- **Pong**
- **Tetris** 
- **Space Invaders**
- **Breakout**
- **Snake**

## Technical Details

### System Specifications

- **Memory**: 4KB (4096 bytes)
- **Display**: 64x32 pixels, monochrome
- **Registers**: 16 general-purpose 8-bit registers (V0-VF)
- **Stack**: 16 levels for subroutines
- **Timers**: 60Hz delay timer and sound timer
- **Input**: 16-key hexadecimal keypad

### Performance Features

- **Numpy-optimized graphics processing** for fast pixel buffer operations
- **SDL2 hardware-accelerated rendering** with VSync
- **Efficient sprite drawing** with collision detection
- **60Hz timing accuracy** for authentic gameplay experience

### Architecture

- **`chip8.py`**: Contains the main CHIP-8 system state using Python dataclasses
- **`cpu.py`**: Implements all CHIP-8 instructions and system operations  
- **`sdl_wrapper.py`**: Handles SDL2 initialization, rendering, and input mapping
- **`common.py`**: Defines error states and utility functions
- **`main.py`**: Main emulation loop with event handling and timing

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'sdl2'"**
   ```bash
   pip install PySDL2 PySDL2-dll
   ```

2. **"could not find any library for SDL2"**
   - Install PySDL2-dll: `pip install PySDL2-dll`
   - On Linux: `sudo apt-get install libsdl2-dev`
   - On macOS: `brew install sdl2`

3. **ROM not loading**
   - Check file path is correct
   - Ensure ROM file has read permissions
   - Verify ROM file is a valid CHIP-8 program

4. **Performance issues**
   - Close other applications to free system resources
   - Update graphics drivers
   - Ensure hardware acceleration is available

### Debug Mode

For debugging, you can add print statements to track execution:

```python
# In main.py, uncomment debug prints in the CPU step section
print(f"PC: {chip8.pc:04X}, Instruction: {instruction:04X}")
```

## Development

### Adding New Features

The modular design makes it easy to extend:

- **New instructions**: Add to `cpu.py` 
- **Audio support**: Extend `sdl_wrapper.py`
- **Different display modes**: Modify rendering in `sdl_wrapper.py`
- **Save states**: Extend `chip8.py` dataclass

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints where appropriate  
- Document new functions with docstrings
- Keep functions focused and modular

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Please respect any ROM copyrights when using this emulator.

## References

- [CHIP-8 Technical Reference](http://devernay.free.fr/hacks/chip8/C8TECH10.HTM)
- [CHIP-8 Instruction Set](https://en.wikipedia.org/wiki/CHIP-8#Opcode_table)
- [SDL2 Documentation](https://wiki.libsdl.org/)
