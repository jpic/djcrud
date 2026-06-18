"""
Reusable attribute descriptors for class and instance access.

This module provides two descriptor classes that work both on classes
and instances, with optional caching behavior.
"""

from functools import update_wrapper
from typing import Any, Callable, Generic, Optional, TypeVar, overload


T = TypeVar('T')
FuncType = Callable[[Any], T]


class cls:
    """
    Descriptor that always returns the class, whether accessed on class or instance.

    This allows code to use self.cls consistently without type checking.

    Examples:
        >>> class MyClass:
        ...     cls = cls()
        ...
        >>> MyClass.cls
        <class 'MyClass'>
        >>> instance = MyClass()
        >>> instance.cls
        <class 'MyClass'>
        >>> instance.cls is MyClass
        True
    """

    def __get__(self, instance, owner):
        """Return the owner class."""
        return owner


class getter(Generic[T]):
    """
    A non-caching property descriptor that works on both classes and instances.

    When accessed on a class, the decorated function receives the class as its
    first argument. When accessed on an instance, it receives the instance.

    The function is called every time the property is accessed (no caching).

    Examples:
        >>> class MyModel:
        ...     @getter
        ...     def table_name(cls):
        ...         '''Return the table name based on class name.'''
        ...         return cls.__name__.lower() + 's'
        ...
        >>> MyModel.table_name
        'mymodels'
        >>> instance = MyModel()
        >>> instance.table_name
        'mymodels'

        >>> class User:
        ...     def __init__(self, name):
        ...         self.name = name
        ...
        ...     @getter
        ...     def identifier(self_or_cls):
        ...         if isinstance(self_or_cls, type):
        ...             return f"Class:{self_or_cls.__name__}"
        ...         return f"Instance:{self_or_cls.name}"
        ...
        >>> User.identifier
        'Class:User'
        >>> User('Alice').identifier
        'Instance:Alice'
    """

    def __init__(self, func: FuncType) -> None:
        """
        Initialize the getter descriptor.

        Args:
            func: The function to be called when the property is accessed.
        """
        self.func = func
        update_wrapper(self, func)

    @overload
    def __get__(self, instance: None, owner: type) -> T:
        ...

    @overload
    def __get__(self, instance: object, owner: type) -> T:
        ...

    def __get__(self, instance: Optional[object], owner: type) -> T:
        """
        Get the property value.

        Args:
            instance: The instance accessing the property, or None if accessed on class.
            owner: The class that owns this descriptor.

        Returns:
            The computed value from calling the wrapped function.
        """
        if instance is None:
            # Accessed on the class
            return self.func(owner)
        else:
            # Accessed on an instance
            return self.func(instance)


class cached(Generic[T]):
    """
    A caching property descriptor that works on both classes and instances.

    Similar to getter, but caches the result:
    - On class access: caches the value on the class itself
    - On instance access: caches the value in the instance's __dict__

    After the first access, subsequent accesses return the cached value
    without calling the function again.

    Examples:
        >>> call_count = 0
        >>> class MyModel:
        ...     @cached
        ...     def expensive_computation(cls):
        ...         '''Perform an expensive computation once.'''
        ...         global call_count
        ...         call_count += 1
        ...         return cls.__name__.upper() * 3
        ...
        >>> call_count
        0
        >>> MyModel.expensive_computation  # First call computes
        'MYMODELMYMODELMYMODEL'
        >>> call_count
        1
        >>> MyModel.expensive_computation  # Second call uses cache
        'MYMODELMYMODELMYMODEL'
        >>> call_count
        1

        >>> class Database:
        ...     def __init__(self, host):
        ...         self.host = host
        ...
        ...     @cached
        ...     def connection_string(self_or_cls):
        ...         if isinstance(self_or_cls, type):
        ...             return "default://localhost"
        ...         return f"postgres://{self_or_cls.host}"
        ...
        >>> Database.connection_string
        'default://localhost'
        >>> db1 = Database('server1.com')
        >>> db1.connection_string
        'postgres://server1.com'
        >>> db2 = Database('server2.com')
        >>> db2.connection_string
        'postgres://server2.com'
        >>> db1.connection_string  # Cached on instance
        'postgres://server1.com'
    """

    def __init__(self, func: FuncType) -> None:
        """
        Initialize the cached descriptor.

        Args:
            func: The function to be called when the property is accessed.
        """
        self.func = func
        self.attrname: Optional[str] = None
        self._class_cache_attr: Optional[str] = None
        update_wrapper(self, func)

    def __set_name__(self, owner: type, name: str) -> None:
        """
        Called when the descriptor is assigned to a class attribute.

        Args:
            owner: The class that owns this descriptor.
            name: The name of the attribute this descriptor is assigned to.
        """
        self.attrname = name
        self._class_cache_attr = f'_cached_classprop_{name}'

    @overload
    def __get__(self, instance: None, owner: type) -> T:
        ...

    @overload
    def __get__(self, instance: object, owner: type) -> T:
        ...

    def __get__(self, instance: Optional[object], owner: type) -> T:
        """
        Get the property value, using cache if available.

        Args:
            instance: The instance accessing the property, or None if accessed on class.
            owner: The class that owns this descriptor.

        Returns:
            The computed or cached value.
        """
        if instance is None:
            # Accessed on the class - cache on the class
            cache_attr = self._class_cache_attr
            if cache_attr is None:
                # __set_name__ wasn't called, fallback to computing without cache
                return self.func(owner)

            if not hasattr(owner, cache_attr):
                # Compute and cache on the class
                value = self.func(owner)
                setattr(owner, cache_attr, value)

            return getattr(owner, cache_attr)
        else:
            # Accessed on an instance - cache in instance.__dict__
            if self.attrname is None:
                # __set_name__ wasn't called, fallback to computing without cache
                return self.func(instance)

            # Check if value is cached in instance __dict__
            instance_dict = instance.__dict__
            if self.attrname not in instance_dict:
                # Compute and cache on the instance
                value = self.func(instance)
                instance_dict[self.attrname] = value

            return instance_dict[self.attrname]


__all__ = ['cls', 'getter', 'cached']
