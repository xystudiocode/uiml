# FAQ

- **Question 1: Why can't I access local variables inside class functions after bundling?**
- - It's because your bundling tool optimizes local variables during packaging, so they can't be recognized. You can fix this by manually registering the `additional` parameter.
- **Question 2: Why can't I use the function and variable features**
- TFor security reasons, we disable variable conversion and function calls *within the library* by default, but this does not affect *Python's default functions*. You can run `set_namespace(enable_value_convert=True)` to fix it.