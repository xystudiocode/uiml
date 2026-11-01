'''NoPaint 特殊值的 GUI 演示。

文件名故意不带 test_ 前缀：该文件会打开窗口并进入 Qt 事件循环，
被 pytest 收集会导致测试挂起。运行方式：

    python tests/no_paint.py

演示内容：
- widget_parser 返回 NoPaint，隐藏指定的 QPushButton；
- layout_parser 返回 NoPaint，隐藏整个 direction="hidden" 的布局；
- 根节点返回 NoPaint 时，UIMLLayout.show() 也返回 NoPaint。
'''
import uiml
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget


uimlcode = '''
<layout name="root" direction="v">
    <QPushButton name="hidden_button" args=['hidden'] />
    <QLabel name="visible_label" args=['visible'] />
    <layout name="hidden_layout" direction="hidden">
        <QLabel name="hidden_nested" args=['hidden nested'] />
    </layout>
    <layout name="visible_layout" direction="h">
        <QLabel name="visible_nested" args=['visible nested'] />
    </layout>
</layout>
'''


def widget_parser(ui_data, namespace, additional):
    if ui_data.get('type') == 'QPushButton' and ui_data.get('name') == 'hidden_button':
        return uiml.NoPaint  # 不绘制，也不会回退到默认组件解析器
    return None


def layout_parser(ui_data, namespace=None, additional=None):
    if str(ui_data.get('direction', '')).lower() == 'hidden':
        return uiml.NoPaint  # 整个布局及其子项都不绘制
    return uiml.default_layout_parser(ui_data, namespace, additional)


def register_parsers():
    uiml.add_parser(uiml.ParserEnum.widget_parser, uiml.ControlEnum.reset)
    uiml.add_parser(uiml.ParserEnum.layout_parser, uiml.ControlEnum.reset)
    uiml.add_parser(uiml.ParserEnum.widget_parser, widget_parser)
    uiml.add_parser(uiml.ParserEnum.layout_parser, layout_parser)


def build():
    '''构建界面但不进入事件循环，方便做无窗口的 smoke test。'''
    app = QApplication.instance() or QApplication([])

    register_parsers()
    data = uiml.compile_ui(uiml.xml_parse(uimlcode))

    window = QWidget()
    window.setWindowTitle('NoPaint demo')
    window.setLayout(uiml.UIMLLayout(data).show())

    return app, window, data


def verify(window, data):
    '''检查 NoPaint 的组件/布局确实没有出现在窗口上。'''
    assert [item.get('name') for item in data['content']] == ['visible_label', 'visible_layout']

    outer = window.layout()
    assert isinstance(outer, QVBoxLayout)
    assert outer.count() == 2

    visible_label = outer.itemAt(0).widget()
    assert isinstance(visible_label, QLabel)
    assert visible_label.text() == 'visible'

    visible_layout = outer.itemAt(1).layout()
    assert visible_layout.count() == 1
    assert visible_layout.itemAt(0).widget().text() == 'visible nested'

    # 被 NoPaint 隐藏的按钮不应被创建
    assert window.findChildren(QPushButton) == []

    # 根节点本身就是 NoPaint 时，show() 返回 NoPaint
    hidden_root = uiml.compile_ui(uiml.xml_parse('''
        <layout name="hidden_root" direction="hidden">
            <QLabel name="hidden_child" args=['hidden'] />
        </layout>
    '''))
    assert hidden_root is uiml.NoPaint
    assert uiml.UIMLLayout(hidden_root).show() is uiml.NoPaint


def main():
    app, window, data = build()
    verify(window, data)
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
