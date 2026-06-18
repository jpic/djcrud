"""
Tests for djcrud.attribute module - cls, getter and cached descriptors.
"""

import pytest
from djcrud.attribute import cls, getter, cached


# Tests for cls descriptor

def test_cls_on_class_returns_class():
    """Accessing cls on class returns the class itself."""
    class MyClass:
        cls = cls()

    assert MyClass.cls is MyClass


def test_cls_on_instance_returns_class():
    """Accessing cls on instance returns the instance's class."""
    class MyClass:
        cls = cls()

    instance = MyClass()
    assert instance.cls is MyClass


def test_cls_with_inheritance():
    """cls descriptor works correctly with inheritance."""
    class Base:
        cls = cls()

    class Child(Base):
        pass

    assert Base.cls is Base
    assert Child.cls is Child

    base_instance = Base()
    child_instance = Child()

    assert base_instance.cls is Base
    assert child_instance.cls is Child


def test_cls_always_returns_same_class():
    """cls always returns the same class reference."""
    class MyClass:
        cls = cls()

    instance1 = MyClass()
    instance2 = MyClass()

    # All return the same class
    assert MyClass.cls is instance1.cls is instance2.cls is MyClass


# Tests for getter descriptor

def test_getter_on_class_receives_class():
    """Accessing getter on class passes the class as argument."""
    call_args = []

    class MyClass:
        @getter
        def my_property(cls_or_self):
            call_args.append(cls_or_self)
            return "class_result"

    result = MyClass.my_property
    assert result == "class_result"
    assert call_args == [MyClass]


def test_getter_on_instance_receives_instance():
    """Accessing getter on instance passes the instance as argument."""
    call_args = []

    class MyClass:
        def __init__(self, value):
            self.value = value

        @getter
        def my_property(cls_or_self):
            call_args.append(cls_or_self)
            return f"instance:{cls_or_self.value}"

    instance = MyClass("test")
    result = instance.my_property
    assert result == "instance:test"
    assert len(call_args) == 1
    assert call_args[0] is instance


def test_getter_no_caching():
    """Getter recomputes value on each access (no caching)."""
    call_count = []

    class MyClass:
        @getter
        def computed(cls):
            call_count.append(1)
            return len(call_count)

    # Access multiple times
    assert MyClass.computed == 1
    assert MyClass.computed == 2
    assert MyClass.computed == 3
    assert len(call_count) == 3


def test_getter_with_isinstance_check():
    """Getter can distinguish between class and instance access."""
    class MyClass:
        @getter
        def identifier(cls_or_self):
            if isinstance(cls_or_self, type):
                return f"Class:{cls_or_self.__name__}"
            return f"Instance:{cls_or_self.__class__.__name__}"

    assert MyClass.identifier == "Class:MyClass"
    assert MyClass().identifier == "Instance:MyClass"


def test_getter_inheritance():
    """Getter works correctly with inheritance."""
    class Base:
        @getter
        def name(cls):
            return cls.__name__

    class Child(Base):
        pass

    assert Base.name == "Base"
    assert Child.name == "Child"


def test_getter_preserves_metadata():
    """Getter preserves function name and docstring."""
    class MyClass:
        @getter
        def documented_property(cls):
            """This is a documented property."""
            return "value"

    descriptor = MyClass.__dict__['documented_property']
    assert descriptor.__name__ == "documented_property"
    assert descriptor.__doc__ == "This is a documented property."


# Tests for cached descriptor

def test_cached_on_class_caches_once():
    """First class access computes and caches, second access uses cache."""
    call_count = []

    class MyClass:
        @cached
        def expensive(cls):
            call_count.append(1)
            return f"computed:{len(call_count)}"

    # First access computes
    result1 = MyClass.expensive
    assert result1 == "computed:1"
    assert len(call_count) == 1

    # Second access uses cache
    result2 = MyClass.expensive
    assert result2 == "computed:1"  # Same value
    assert len(call_count) == 1  # Not called again


def test_cached_on_instance_caches_in_dict():
    """Instance access caches value in instance.__dict__."""
    call_count = []

    class MyClass:
        def __init__(self, value):
            self.value = value

        @cached
        def expensive(self):
            call_count.append(1)
            return f"computed:{self.value}:{len(call_count)}"

    instance = MyClass("test")

    # First access computes
    result1 = instance.expensive
    assert result1 == "computed:test:1"
    assert len(call_count) == 1

    # Second access uses cache from __dict__
    result2 = instance.expensive
    assert result2 == "computed:test:1"
    assert len(call_count) == 1

    # Check it's in __dict__
    assert "expensive" in instance.__dict__
    assert instance.__dict__["expensive"] == "computed:test:1"


def test_cached_separate_cache_per_instance():
    """Different instances have separate caches."""
    call_count = []

    class MyClass:
        def __init__(self, value):
            self.value = value

        @cached
        def expensive(self):
            call_count.append(1)
            return f"result:{self.value}"

    instance1 = MyClass("one")
    instance2 = MyClass("two")

    assert instance1.expensive == "result:one"
    assert instance2.expensive == "result:two"
    assert len(call_count) == 2  # Called once per instance

    # Second accesses use cache
    assert instance1.expensive == "result:one"
    assert instance2.expensive == "result:two"
    assert len(call_count) == 2  # Still only 2 calls


def test_cached_class_and_instance_separate():
    """Class and instance caches are separate."""
    call_count = []

    class MyClass:
        @cached
        def expensive(cls_or_self):
            call_count.append(1)
            if isinstance(cls_or_self, type):
                return f"class_result:{len(call_count)}"
            return f"instance_result:{len(call_count)}"

    # Access from class
    result1 = MyClass.expensive
    assert result1 == "class_result:1"
    assert len(call_count) == 1

    # Access from instance - separate cache, calls function again
    instance = MyClass()
    result2 = instance.expensive
    assert result2 == "instance_result:2"
    assert len(call_count) == 2  # Called again for instance


def test_cached_inheritance_on_instances():
    """Subclass instances get their own cache storage."""
    call_count = []

    class Base:
        def __init__(self, value):
            self.value = value

        @cached
        def expensive(self):
            call_count.append(1)
            return f"{self.__class__.__name__}:{self.value}"

    class Child(Base):
        pass

    # Create instances
    base_instance = Base("base_val")
    child_instance = Child("child_val")

    # Access on base instance
    assert base_instance.expensive == "Base:base_val"
    assert len(call_count) == 1

    # Access on child instance - separate cache
    assert child_instance.expensive == "Child:child_val"
    assert len(call_count) == 2

    # Subsequent accesses use instance cache
    assert base_instance.expensive == "Base:base_val"
    assert child_instance.expensive == "Child:child_val"
    assert len(call_count) == 2


def test_cached_set_name_stores_attribute_name():
    """__set_name__ is called and stores the attribute name."""
    class MyClass:
        @cached
        def my_attr(cls):
            return "value"

    descriptor = MyClass.__dict__['my_attr']
    assert descriptor.attrname == "my_attr"
    assert descriptor._class_cache_attr == "_cached_classprop_my_attr"


def test_cached_preserves_metadata():
    """Cached preserves function name and docstring."""
    class MyClass:
        @cached
        def documented_cached(cls):
            """This is a cached property."""
            return "value"

    descriptor = MyClass.__dict__['documented_cached']
    assert descriptor.__name__ == "documented_cached"
    assert descriptor.__doc__ == "This is a cached property."


def test_cached_with_isinstance_check():
    """Cached can distinguish between class and instance access."""
    call_count = []

    class MyClass:
        def __init__(self, name):
            self.name = name

        @cached
        def identifier(cls_or_self):
            call_count.append(1)
            if isinstance(cls_or_self, type):
                return f"Class:{cls_or_self.__name__}"
            return f"Instance:{cls_or_self.name}"

    # Access from class - cached
    assert MyClass.identifier == "Class:MyClass"
    assert len(call_count) == 1
    assert MyClass.identifier == "Class:MyClass"
    assert len(call_count) == 1  # Used cache

    # Access from instance - separate cache
    instance = MyClass("test")
    assert instance.identifier == "Instance:test"
    assert len(call_count) == 2
    assert instance.identifier == "Instance:test"
    assert len(call_count) == 2  # Used instance cache
