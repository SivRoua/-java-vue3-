from .auth import auth_bp
from .device_control import device_bp
from .history import history_bp
from .alerts import alerts_bp

__all__ = ['auth_bp', 'device_bp', 'history_bp', 'alerts_bp']