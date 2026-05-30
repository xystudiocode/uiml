<div align="center">
<img src="./imgs/readme/logo.png" width="400" alt="logo" />
<h1>uiml</h1>
一个使用特殊的xml格式，用于绘制PySide6的ui界面
</div>
<br />
<div align = "center">
    <a href="https://github.com/xystudiocode/uiml/actions?query=workflow%3Adeploy">
        <img src="https://github.com/xystudiocode/uiml/workflows/deploy/badge.svg"
            alt="deploy">
    </a>
    <a href="https://github.com/xystudiocode/uiml/actions?query=workflow%3Atest">
        <img src="https://github.com/xystudiocode/uiml/workflows/test/badge.svg"
            alt="test">
    </a>
    <a href="https://pypi.org/project/uiml/">
        <img src="https://img.shields.io/pypi/v/uiml.svg" 
        alt="pypi">
    </a>
    <a href="https://img.shields.io/pypi/pyversions/uiml">
        <img src="https://img.shields.io/pypi/pyversions/uiml" alt="support-version">
    </a>
    <a href="https://github.com/xystudiocode/uiml/blob/master/LICENSE">
        <img src="https://img.shields.io/github/license/xystudiocode/uiml.svg" alt="license">
    </a>
    <a href="https://github.com/xystudiocode/uiml/commits/main">
        <img src="https://img.shields.io/github/last-commit/xystudiocode/uiml/main" alt="commit">
    </a>
</div>
<br />
<div align="center" style="line-height: 1;">
  <a href="./README.md"><img
    src="https://img.shields.io/badge/language-English-536af5?color=781ff1&logoColor=white"/></a>
  <a href="./README-ZH_CN.md"><img
    src="https://img.shields.io/badge/简体中文-536af5?color=ff0000&logoColor=white"/></a>
</div>
<br />

--- 

## 介绍
uiml是一个用于绘制PySide6的ui界面的工具，它使用特殊的xml格式来定义界面的布局，样式和信号。uiml的语法非常简单，易于学习和使用。你可以使用uiml来创建复杂的界面，而不需要编写大量的代码。

uiml的语法在xml的基础上，增加支持的python对象，所以它既有xml的轻便性，又有python对象的灵活性。

## 安装
要使用uiml，你需要先安装它。你可以使用pip来安装uiml：

```bash
pip install uiml
```

## 使用
要使用uiml，你需要创建一个uiml文件，并在其中定义界面的布局，样式和信号。以下是一个简单的示例：

```xml
<layout name="central_layout" direction="v">
    <QLabel name="text" arg=["This is a label"] />
    <layout name="bottom_layout" direction="h" stretch="true">
        <QPushButton name="ok_button" arg=["Close the window"] style="selected" signals={"clicked": self.close} />
    </layout>
</layout>
```

## 属性
### layout
这是布局对象，可以在子项添加布局对象，或者添加控件对象。
参数：
- name：布局对象的名称，用于在代码中引用。
- direction：布局的方向，可以是“v”（垂直）或“h”（水平），可以自己扩展。
- stretch：布局对象的拉伸因子，可以是“true”或“false”。

### Widget
这是组件对象，对象的tag名是控件的名称，例如“QLabel”、“QPushButton”等。
参数：
- name：控件对象的名称，用于在代码中引用。
- arg：控件对象的参数，使用列表存储，可以是字符串、列表、字典等。
- kwarg：控件对象的属性，带有关键字，使用字典存储，可以是字符串、列表、字典等。
- style：控件对象的样式，可以是字符串、列表、字典等。
- signals：控件对象的信号，使用字典存储，键是信号名称，值是信号处理函数。
- init_steps：控件对象的初始化步骤，使用列表存储，子项使用字典。
