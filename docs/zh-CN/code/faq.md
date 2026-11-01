# FAQ

- **问题1：为什么我用打包工具打包后，无法识别类函数内部的local变量？**
- - 这是因为你的打包工具在打包过程中，把local变量给优化了，所以无法识别。你可以手动注册`additional`参数，来解决这个问题。
- **问题2：为什么我无法使用函数和变量功能**
- - 这是因为为了安全性，我们默认禁用了*库内的*变量转换和函数调用，但是不影响*python默认函数*。新版本可以运行 `uiml.set_config(uiml.ParamEnum.value_convert, True)` 来解决，详见[自定义（新版本）](./parser.md)；旧版本 Namespace API 的写法是 `uiml.enable_namespace_api()` 后 `uiml.set_namespace(enable_value_convert=True)`，详见[自定义（旧版本）](./custom.md)。