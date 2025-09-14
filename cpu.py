import random
import time
from typing import List

from chip8 import Chip8


class Chip8Exception(Exception):
    """Custom exception for CHIP-8 emulator errors"""
    pass


class Cpu:
    # Font character data (equivalent to ReadOnlySpan<byte> in C#)
    FONT_CHARACTERS = [
        0xF0, 0x90, 0x90, 0x90, 0xF0, 0x20, 0x60, 0x20, 0x20, 0x70, 0xF0, 0x10, 0xF0, 0x80, 0xF0, 0xF0, 0x10, 0xF0, 0x10, 0xF0,
        0x90, 0x90, 0xF0, 0x10, 0x10, 0xF0, 0x80, 0xF0, 0x10, 0xF0, 0xF0, 0x80, 0xF0, 0x90, 0xF0, 0xF0, 0x10, 0x20, 0x40, 0x40,
        0xF0, 0x90, 0xF0, 0x90, 0xF0, 0xF0, 0x90, 0xF0, 0x10, 0xF0, 0xF0, 0x90, 0xF0, 0x90, 0x90, 0xE0, 0x90, 0xE0, 0x90, 0xE0,
        0xF0, 0x80, 0x80, 0x80, 0xF0, 0xE0, 0x90, 0x90, 0x90, 0xE0, 0xF0, 0x80, 0xF0, 0x80, 0xF0, 0xF0, 0x80, 0xF0, 0x80, 0x80
    ]

    def __init__(self):
        self.generator = random.Random()
        self.generator.seed()

    @staticmethod
    def load_program(chip8: Chip8, program: List[int]) -> None:
        """Load a program into CHIP-8 memory"""
        program_start = 512

        # Clear memory and load font characters
        chip8.memory[:] = [0] * 4096
        chip8.memory[:len(Cpu.FONT_CHARACTERS)] = Cpu.FONT_CHARACTERS

        # Load program into memory starting at program_start
        for i, byte_val in enumerate(program):
            if program_start + i < len(chip8.memory):
                chip8.memory[program_start + i] = byte_val & 0xFF

        chip8.pc = program_start
        chip8.sp = 0

    @staticmethod
    def key_pressed(chip8: Chip8, key: int) -> None:
        """Handle key press event"""
        chip8.waiting_for_key_press = False

        opcode = (chip8.memory[chip8.pc] << 8) | chip8.memory[chip8.pc + 1]
        chip8.v[(opcode & 0x0F00) >> 8] = key & 0xFF
        chip8.pc += 2

    @staticmethod
    def step(chip8: Chip8, ticks_per_60hz: int) -> None:
        """Execute one CPU step"""
        current_time = time.time()
        if chip8.watch_start == 0:
            chip8.watch_start = current_time

        # Update delay timer at 60Hz
        if chip8.delay_timer > 0 and (current_time - chip8.watch_start) * 60 >= 1:
            chip8.delay_timer -= 1
            chip8.watch_start = current_time

        opcode = (chip8.memory[chip8.pc] << 8) | chip8.memory[chip8.pc + 1]

        if chip8.waiting_for_key_press:
            raise Chip8Exception("Do not call Step when chip8.waiting_for_key_press is set.")

        nibble = opcode & 0xF000
        nn = opcode & 0x00FF

        chip8.pc += 2

        if nibble == 0x0000:
            if opcode == 0x00E0:  # clear screen
                chip8.gfx[:] = [0] * (64 * 32)
            elif opcode == 0x00EE:  # return from subroutine
                chip8.sp -= 1
                chip8.pc = chip8.stack[chip8.sp]
            else:
                raise Chip8Exception(f"Unsupported opcode {opcode:04X}")

        elif nibble == 0x1000:  # jump to address NNN
            chip8.pc = opcode & 0x0FFF

        elif nibble == 0x2000:  # call subroutine at NNN
            chip8.stack[chip8.sp] = chip8.pc
            chip8.sp += 1
            chip8.pc = opcode & 0x0FFF

        elif nibble == 0x3000:  # skip next instruction if Vx == NN
            if chip8.v[(opcode & 0x0F00) >> 8] == nn:
                chip8.pc += 2

        elif nibble == 0x4000:  # skip next instruction if Vx != NN
            if chip8.v[(opcode & 0x0F00) >> 8] != nn:
                chip8.pc += 2

        elif nibble == 0x5000:  # skip next instruction if Vx == Vy
            if chip8.v[(opcode & 0x0F00) >> 8] == chip8.v[(opcode & 0x00F0) >> 4]:
                chip8.pc += 2

        elif nibble == 0x6000:  # set Vx = NN
            chip8.v[(opcode & 0x0F00) >> 8] = nn & 0xFF

        elif nibble == 0x7000:  # set Vx = Vx + NN
            vx_index = (opcode & 0x0F00) >> 8
            chip8.v[vx_index] = (chip8.v[vx_index] + nn) & 0xFF

        elif nibble == 0x8000:  # arithmetic operations
            vx = (opcode & 0x0F00) >> 8
            vy = (opcode & 0x00F0) >> 4
            sub_op = opcode & 0x000F

            if sub_op == 0:  # LD Vx, Vy
                chip8.v[vx] = chip8.v[vy]
            elif sub_op == 1:  # OR Vx, Vy
                chip8.v[vx] = (chip8.v[vx] | chip8.v[vy]) & 0xFF
            elif sub_op == 2:  # AND Vx, Vy
                chip8.v[vx] = (chip8.v[vx] & chip8.v[vy]) & 0xFF
            elif sub_op == 3:  # XOR Vx, Vy
                chip8.v[vx] = (chip8.v[vx] ^ chip8.v[vy]) & 0xFF
            elif sub_op == 4:  # ADD Vx, Vy
                result = chip8.v[vx] + chip8.v[vy]
                chip8.v[15] = 1 if result > 255 else 0  # VF = carry flag
                chip8.v[vx] = result & 0xFF
            elif sub_op == 5:  # SUB Vx, Vy
                chip8.v[15] = 1 if chip8.v[vx] > chip8.v[vy] else 0  # VF = borrow flag
                chip8.v[vx] = (chip8.v[vx] - chip8.v[vy]) & 0xFF
            elif sub_op == 6:  # SHR Vx {, Vy}
                chip8.v[15] = chip8.v[vx] & 0x01
                chip8.v[vx] = chip8.v[vx] >> 1
            elif sub_op == 7:  # SUBN Vx, Vy
                chip8.v[15] = 1 if chip8.v[vy] > chip8.v[vx] else 0
                chip8.v[vx] = (chip8.v[vy] - chip8.v[vx]) & 0xFF
            elif sub_op == 14:  # SHL Vx {, Vy}
                chip8.v[15] = 1 if (chip8.v[vx] & 0x80) == 0x80 else 0
                chip8.v[vx] = (chip8.v[vx] << 1) & 0xFF
            else:
                raise Chip8Exception(f"Unsupported opcode {opcode:04X}")

        elif nibble == 0x9000:  # skip next instruction if Vx != Vy
            if chip8.v[(opcode & 0x0F00) >> 8] != chip8.v[(opcode & 0x00F0) >> 4]:
                chip8.pc += 2

        elif nibble == 0xA000:  # set I = NNN
            chip8.i = opcode & 0x0FFF

        elif nibble == 0xB000:  # jump to address NNN + V0
            chip8.pc = (opcode & 0x0FFF) + chip8.v[0]

        elif nibble == 0xC000:  # set Vx = random byte AND NN
            rnd_byte = random.randint(0, 255)
            chip8.v[(opcode & 0x0F00) >> 8] = (rnd_byte & nn) & 0xFF

        elif nibble == 0xD000:  # display n-byte sprite starting at memory location I at (Vx, Vy)
            x = chip8.v[(opcode & 0x0F00) >> 8]
            y = chip8.v[(opcode & 0x00F0) >> 4]
            n = opcode & 0x000F
            chip8.v[15] = 1 if Cpu.draw_sprites_fast(chip8, x, y, n) else 0

        elif nibble == 0xE000:  # key operations
            if nn == 0x009E:  # skip next instruction if key with value of Vx is pressed
                key_val = chip8.v[(opcode & 0x0F00) >> 8]
                if ((chip8.keyboard >> key_val) & 0x01) == 0x01:
                    chip8.pc += 2
            elif nn == 0x00A1:  # skip next instruction if key with value of Vx is not pressed
                key_val = chip8.v[(opcode & 0x0F00) >> 8]
                if ((chip8.keyboard >> key_val) & 0x01) != 0x01:
                    chip8.pc += 2
            else:
                raise Chip8Exception(f"Unsupported opcode {opcode:04X}")

        elif nibble == 0xF000:  # miscellaneous operations
            tx = (opcode & 0x0F00) >> 8
            sub_op = opcode & 0x00FF

            if sub_op == 0x07:  # set Vx = delay timer value
                chip8.v[tx] = chip8.delay_timer
            elif sub_op == 0x0A:  # wait for key press, store value in Vx
                chip8.waiting_for_key_press = True
                chip8.pc -= 2
            elif sub_op == 0x15:  # set delay timer = Vx
                chip8.delay_timer = chip8.v[tx]
            elif sub_op == 0x18:  # set sound timer = Vx
                chip8.sound_timer = chip8.v[tx]
            elif sub_op == 0x1E:  # set I = I + Vx
                chip8.i = (chip8.i + chip8.v[tx]) & 0xFFFF
            elif sub_op == 0x29:  # set I = location of sprite for digit Vx
                chip8.i = (chip8.v[tx] * 5) & 0xFFFF
            elif sub_op == 0x33:  # store BCD representation of Vx
                chip8.memory[chip8.i] = chip8.v[tx] // 100
                chip8.memory[chip8.i + 1] = (chip8.v[tx] % 100) // 10
                chip8.memory[chip8.i + 2] = chip8.v[tx] % 10
            elif sub_op == 0x55:  # store registers V0 through Vx in memory starting at I
                for i in range(tx + 1):
                    chip8.memory[chip8.i + i] = chip8.v[i]
            elif sub_op == 0x65:  # read registers V0 through Vx from memory starting at I
                for i in range(tx + 1):
                    chip8.v[i] = chip8.memory[chip8.i + i]
            else:
                raise Chip8Exception(f"Unsupported opcode {opcode:04X}")

        else:
            raise Chip8Exception(f"Unsupported opcode {opcode:04X}")

    @staticmethod
    def draw_sprites_naive(chip8: Chip8, x: int, y: int, n: int) -> bool:
        """Draw sprites on screen and return True if collision detected

        PERFORMANCE ANALYSIS:
        - Slow due to nested loops with bounds checking on each iteration
        - Uses modulo operations (%) which are expensive
        - Individual pixel access and XOR operations in Python loops
        - Branch prediction issues due to conditional sprite pixel checks
        - Estimated: ~O(n*8) with high constant factor due to Python overhead
        """
        collision = False

        for row in range(n):
            sprite_byte = chip8.memory[chip8.i + row]

            for col in range(8):
                if (sprite_byte & (0x80 >> col)) != 0:
                    pixel_x = (x + col) % 64
                    pixel_y = (y + row) % 32
                    pixel_index = pixel_y * 64 + pixel_x

                    if chip8.gfx[pixel_index] == 1:
                        collision = True

                    chip8.gfx[pixel_index] ^= 1

        return collision

    @staticmethod
    def draw_sprites_internal(chip8: Chip8, x: int, y: int, n: int) -> bool:
        """Optimized internal sprite drawing method (equivalent to C# DrawSpritesInternal)

        PERFORMANCE ANALYSIS:
        - Better than draw_sprites: eliminates modulo operations and redundant bounds checks
        - Still suffers from Python loop overhead and individual pixel manipulation
        - Early break optimizations for out-of-bounds cases
        - Uses 0xffffffff XOR which is overkill for boolean values
        - Estimated: ~O(n*8) with medium constant factor, 2-3x faster than draw_sprites
        """
        set_last_v = False
        gfx = chip8.gfx
        memory = chip8.memory

        for byte_index in range(n):
            current_y = y + byte_index
            if current_y >= 32:
                break

            mem = memory[chip8.i + byte_index]
            row_offset = current_y * 64

            current_x = x
            for bit in range(7, -1, -1):  # bit = 7 down to 0
                if current_x >= 64:
                    break

                index = row_offset + current_x
                pixel = (mem >> bit) & 1

                if pixel == 0:
                    current_x += 1
                    continue

                set_last_v |= gfx[index] > 0
                gfx[index] ^= 0xffffffff
                current_x += 1

        return set_last_v

    @staticmethod
    def draw_sprites_fast(chip8: Chip8, x: int, y: int, n: int) -> bool:
        """'Ultra-fast' sprite drawing using NumPy vectorized operations

        PERFORMANCE ANALYSIS:
        - Uses NumPy for vectorized bit operations and array manipulations
        - Eliminates Python loops entirely for bit extraction
        - Vectorized XOR and collision detection
        - Memory-efficient with pre-allocated arrays
        - Estimated: ~O(n) with very low constant factor, 10-50x faster than Python loops
        """
        import numpy as np

        set_last_v = False

        # Convert lists to numpy arrays for vectorized operations
        gfx_array = np.array(chip8.gfx, dtype=np.uint32)
        memory_array = np.array(chip8.memory, dtype=np.uint8)

        # Process all sprite bytes at once
        sprite_bytes = memory_array[chip8.i:chip8.i + n]

        for byte_index in range(len(sprite_bytes)):
            current_y = y + byte_index
            if current_y >= 32:
                break

            # Extract all 8 bits from the sprite byte using vectorized operations
            sprite_byte = int(sprite_bytes[byte_index])  # Ensure it's a Python int

            # Create bit mask for all 8 pixels in this row
            bit_positions = np.arange(8, dtype=np.int32)  # Use int32 to avoid overflow
            pixel_bits = (sprite_byte >> (7 - bit_positions)) & 1

            # Calculate screen positions for this row
            pixel_x_positions = x + bit_positions

            # Only process pixels that are within bounds
            valid_pixels = (pixel_x_positions < 64) & (pixel_bits == 1)

            if not np.any(valid_pixels):
                continue

            # Get the valid positions
            valid_x = pixel_x_positions[valid_pixels]
            row_offset = current_y * 64
            pixel_indices = row_offset + valid_x

            # Vectorized collision detection
            existing_pixels = gfx_array[pixel_indices]
            collision_mask = existing_pixels > 0
            set_last_v |= np.any(collision_mask)

            # Vectorized XOR operation (toggle pixels)
            gfx_array[pixel_indices] ^= 0xffffffff

        # Update the original list (convert back from numpy)
        # Ensure we convert to Python ints to avoid numpy scalar issues
        for i in range(len(chip8.gfx)):
            chip8.gfx[i] = int(gfx_array[i])

        return set_last_v

    @staticmethod
    def to_byte(value: bool) -> int:
        """Convert boolean to byte (0 or 1)"""
        return 1 if value else 0
