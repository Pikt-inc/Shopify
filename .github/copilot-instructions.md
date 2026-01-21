# Copilot Instructions

## General Guidelines

1. **Strong Typing**: All functions must be strongly typed. Use Python type hints for all parameters and return types.
   - Example:
     ```python
     def example_function(param1: int, param2: str) -> bool:
         pass
     ```

2. **Docstrings**: Every function must include a comprehensive docstring that explains:
   - The purpose of the function.
   - Each parameter, including its type and purpose.
   - The return value, including its type and meaning.
   - Example:
     ```python
     def example_function(param1: int, param2: str) -> bool:
         """
         Example function that demonstrates the required docstring format.

         :param param1: An integer representing the first parameter.
         :type param1: int
         :param param2: A string representing the second parameter.
         :type param2: str
         :return: A boolean indicating success or failure.
         :rtype: bool
         """
         pass
     ```

3. **Validation Decorator**: All functions must use the `@validate_call(validate_return=True)` decorator to enforce strong typing and validate return values.
   - Example:
     ```python
     @validate_call(validate_return=True)
     def example_function(param1: int, param2: str) -> bool:
         pass
     ```

4. **Error Handling**: Ensure proper error handling for all functions. Raise meaningful exceptions with clear messages when errors occur.
   - Example:
     ```python
     if some_error_condition:
         raise ValueError("A clear and descriptive error message.")
     ```

5. **Code Style**: Follow PEP 8 guidelines for code formatting and style. Use tools like `ruff format` and `ruff check . --fix` to enforce consistency.

6. **Imports**: Organize imports into three sections: standard library, third-party libraries, and local modules. Use `isort` to maintain order.

7. **Testing**: Write unit tests for all functions to ensure correctness. Use `pytest` as the testing framework.

8. **Logging**: Use the `logging` module for debug and error messages instead of `print` statements.

## Example Function Template

```python
@validate_call(validate_return=True)
def example_function(param1: int, param2: str) -> bool:
    """
    Example function that demonstrates the required structure.

    :param param1: An integer representing the first parameter.
    :type param1: int
    :param param2: A string representing the second parameter.
    :type param2: str
    :return: A boolean indicating success or failure.
    :rtype: bool
    """
    # Function implementation goes here
    pass
```