import time
from dataclasses import dataclass, field
from typing import List

@dataclass
class Chip8:
    memory: List[int] = field(default_factory=lambda: [0] * 4096)    # 4K memory
    v: List[int] = field(default_factory=lambda: [0] * 16)           # registers V0 to VF
    gfx: List[int] = field(default_factory=lambda: [0] * (64 * 32))  # graphics (64x32 pixels)
    stack: List[int] = field(default_factory=lambda: [0] * 16)       # call stack
    sp: int = 0                                                      # stack pointer
    pc: int = 0                                                      # program counter
    i: int = 0                                                       # index
    delay_timer: int = 0                                             # delay
    sound_timer: int = 0                                             # sound
    keyboard: int = 0                                                # hex keyboard state
    waiting_for_key_press: bool = False                              # true if waiting for a key press to store in Vx
    watch_start: float = field(default_factory=time.time)            # timer for 60Hz updates
