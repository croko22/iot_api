
class AppState:
    _instance = None
    is_fire_detected: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppState, cls).__new__(cls)
        return cls._instance

state = AppState()
