from typing import Dict, Any


class SingletonMeta(type):
    """
    A metaclass for creating singleton classes.
    Ensures that only one instance of the class exists per unique key.
    """
    _instances: Dict[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        # Use the access token as the key for the singleton lookup
        key = kwargs.get("access_token")
        if key is None:
            raise ValueError("An 'access_token' must be provided to create a singleton instance.")

        if key not in cls._instances:
            # If an instance does not already exist for the key, create one and store it
            instance = super().__call__(*args, **kwargs)
            cls._instances[key] = instance
        return cls._instances[key]


class SingletonBase(metaclass=SingletonMeta):
    """
    Base class for creating singleton objects.
    Inherit from this class to make a class a singleton.
    """
    pass