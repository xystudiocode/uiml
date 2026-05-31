# 参数
## Layout
layout是一个布局对象，里面定义了组件

- `name`：布局的名称，可以在代码中引用
- `direction`：布局的方向，可以是`v`（垂直）或`h`（水平），也可以自定义。
- `stretch`：布局的伸展属性，可以是`true`或`false`

## Widget
widget是一个组件对象，里面定义了组件的属性

tag名字需要设置成Qt的标签名，例如`QLabel`、`QPushButton`等。

- `name`：组件的名称，可以在代码中引用
- `args`：组件的参数，可以是字符串、列表、字典等
- `kwargs`：组件的关键字参数，可以是字符串、列表、字典等
- `init_steps`: 组件的初始化步骤，可以是列表，例如`[{"name": "function", "arg": ["value"], "kwarg": {"style": "selected"}}]`
- `style`：组件的样式类名，可以是字符串，例如`big_text`等
- `signals`：组件的信号，可以是字典，例如`'clicked': self.close`