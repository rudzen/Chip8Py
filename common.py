from enum import Flag

class StateError(Flag):
    NONE = 0
    SDL_INIT = 1
    WINDOW_CREATE = 2
    RENDERER_CREATE = 4
    FILE_LOAD = 8
    AUDIO_INIT = 16


class StateErrorExtensions:
    @staticmethod
    def has_flag_fast(value: StateError, flag: StateError) -> bool:
        return (value & flag) != StateError.NONE
