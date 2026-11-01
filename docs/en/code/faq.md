# FAQ

- **Question 1: Why can't I access local variables inside class functions after bundling?**
- - It's because your bundling tool optimizes local variables during packaging, so they can't be recognized. You can fix this by manually registering the `additional` parameter.
- **Question 2: Why can't I use the function and variable features**
- For security reasons, we disable variable conversion and function calls *within the library* by default, but this does not affect *Python's default functions*. In the new version, run `uiml.set_config(uiml.ParamEnum.value_convert, True)`; see [Customization (New Version)](./parser.md). With the old Namespace API, run `uiml.enable_namespace_api()` and then `uiml.set_namespace(enable_value_convert=True)`; see [Customization (Old Version)](./custom.md).