"""Windows process creation flags for detached background execution without visible console windows."""

CREATE_NEW_PROCESS_GROUP: int = 0x00000200
CREATE_NO_WINDOW: int = 0x08000000
