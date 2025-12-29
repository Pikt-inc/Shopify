from typing import Dict, Any


class SingletonMeta(type):
    """
    A metaclass for creating singleton classes.
    Ensures that only one instance of the class exists per unique key.
    """

    _instances: Dict[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        # Use shop_domain, access_token, and api_version to avoid cross-shop collisions.
        shop_domain = kwargs.get("shop_domain")
        access_token = kwargs.get("access_token")
        api_version = kwargs.get("api_version")
        if shop_domain is None and len(args) >= 1:
            shop_domain = args[0]
        if access_token is None and len(args) >= 2:
            access_token = args[1]
        if api_version is None and len(args) >= 3:
            api_version = args[2]
        if access_token is None:
            raise ValueError(
                "An 'access_token' must be provided to create a singleton instance."
            )
        if shop_domain is None:
            raise ValueError(
                "A 'shop_domain' must be provided to create a singleton instance."
            )

        key = (shop_domain, access_token, api_version)
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
