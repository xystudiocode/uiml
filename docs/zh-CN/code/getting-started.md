# 开始使用
## 安装
使用pip安装uiml：

```bash
pip install uiml
```

## 创建uiml文件
uiml文件是一个XML文件，用于定义界面的布局，样式和信号。你可以使用任何文本编辑器创建uiml文件。以下是一个简单的示例：

```xml
<layout name="central_layout" direction="v">
    <QLabel name="text" args=["This is a label"] />
    <layout name="bottom_layout" direction="h" stretch="true">
        <QPushButton name="ok_button" args=["Close the window"] style="selected" signals={"clicked": self.close} />
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

<img src="/imgs/demo/1.png" width="200px" />