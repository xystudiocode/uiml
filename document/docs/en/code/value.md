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
- `arg`：组件的参数，可以是字符串、列表、字典等
- `kwarg`：组件的关键字参数，可以是字符串、列表、字典等
- `init_steps`: 组件的初始化步骤，可以是列表，例如`[{"name": "function", "arg": ["value"], "kwarg": {"style": "selected"}}]`
- `style`：组件的样式类名，可以是字符串，例如`big_text`等
- `signals`：组件的信号，可以是字典，例如`'clicked': self.close`

```bash
pip install uiml
```

## 创建uiml文件
uiml文件是一个XML文件，用于定义界面的布局，样式和信号。你可以使用任何文本编辑器创建uiml文件。以下是一个简单的示例：

```xml
<layout name="central_layout" direction="v">
    <QLabel name="text" arg=["This is a label"] />
    <layout name="bottom_layout" direction="h" stretch="true">
        <QPushButton name="ok_button" arg=["Close the window"] style="selected" signals={"clicked": self.close} />
    </layout>
</layout>
```

然后你把代码保存为一个uiml文件，例如`central_layout.uiml`。

## 加载uiml文件
你可以使用uiml库加载uiml文件并创建界面。以下是一个简单的示例：

```python
import uiml

# 初始化应用
app = uiml.QApplication()
widget = uiml.QWidget()

# 加载uiml文件
layout = uiml.UIMLLayout(uiml.compile_ui_file("central_layout.uiml")).show() # 从文件读取布局数据，然后解析并绘制布局

# 设置布局
widget.setLayout(layout)

# 显示界面
widget.show()

# 运行应用
app.exec()
```

如果运行成功，那么将会显示一个包含一个标签和一个按钮的界面。点击按钮将会关闭窗口。

应该会显示：

<img src="\imgs\demo\1.png" width="200px" />