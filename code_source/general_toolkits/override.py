#!/usr/bin/env python3

def override(method):
    # Get the class of the method
    cls = method.__self__.__class__
    
    # Look for a method with the same name in the parent classes
    if not any(
        method.__name__ in cls.__bases__[0].__dict__ for cls in cls.__mro__[1:]
    ):
        raise TypeError(f"Method {method.__name__} is not overriding any method.")
    
    return method

