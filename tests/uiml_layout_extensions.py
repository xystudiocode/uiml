'''多个 UIMLLayout 扩展类的 GUI 演示。

文件名故意不带 test_ 前缀：该文件会打开窗口并进入 Qt 事件循环，
被 pytest 收集会导致测试挂起。运行方式：

    python tests/uiml_layout_extensions.py

演示内容：
- 定义两个 UIMLLayout 扩展类，分别用 QHBoxLayout 和 QVBoxLayout 渲染布局；
- 通过 Parser API 同时注册两个扩展的工厂函数；
- 在同一个窗口中同时展示两种扩展布局。
'''
import uiml
from PySide6.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget


horizontal_uiml = '''
<layout name="horizontal_root" direction="x">
    <QLabel name="h1" args=['H1'] />
    <QLabel name="h2" args=['H2'] />
</layout>
'''

vertical_uiml = '''
<layout name="vertical_root" direction="y">
    <QLabel name="v1" args=['V1'] />
    <QLabel name="v2" args=['V2'] />
</layout>
'''


class HorizontalExtension(uiml.UIMLLayout):
    '''扩展类 1：把 direction="x" 渲染成水平布局。'''

    def extend_layout(self, list_info):
        if str(list_info.get('direction', '')).lower() == 'x':
            layout = QHBoxLayout()
            self._for_loop(list_info, layout)
            return layout, 'layout'
        return super().extend_layout(list_info)


class VerticalExtension(uiml.UIMLLayout):
    '''扩展类 2：把 direction="y" 渲染成垂直布局。'''

    def extend_layout(self, list_info):
        if str(list_info.get('direction', '')).lower() == 'y':
            layout = QVBoxLayout()
            self._for_loop(list_info, layout)
            return layout, 'layout'
        return super().extend_layout(list_info)


def horizontal_parser(list_data):
    if str(list_data.get('direction', '')).lower() == 'x':
        return HorizontalExtension(list_data)
    return None


def vertical_parser(list_data):
    if str(list_data.get('direction', '')).lower() == 'y':
        return VerticalExtension(list_data)
    return None


def register_extensions():
    # 用工厂函数按 direction 选择扩展类：直接注册两个类时，后注册的类会接管全部数据。
    uiml.add_parser(uiml.ParserEnum.uiml_class, uiml.ControlEnum.reset)
    uiml.add_parser(uiml.ParserEnum.uiml_class, horizontal_parser)
    uiml.add_parser(uiml.ParserEnum.uiml_class, vertical_parser)


def build():
    '''构建界面但不进入事件循环，方便做无窗口的 smoke test。'''
    app = QApplication.instance() or QApplication([])

    register_extensions()

    horizontal_data = uiml.compile_ui(uiml.xml_parse(horizontal_uiml))
    vertical_data = uiml.compile_ui(uiml.xml_parse(vertical_uiml))

    # 两次构造分别命中两个不同的扩展类
    horizontal_layout = uiml.UIMLLayout(horizontal_data).show()
    vertical_layout = uiml.UIMLLayout(vertical_data).show()

    window = QWidget()
    window.setWindowTitle('Multiple UIMLLayout extensions')

    outer = QVBoxLayout()
    outer.addWidget(QLabel('Horizontal extension (direction="x") -> QHBoxLayout'))
    outer.addLayout(horizontal_layout)
    outer.addWidget(QLabel('Vertical extension (direction="y") -> QVBoxLayout'))
    outer.addLayout(vertical_layout)
    window.setLayout(outer)

    return app, window


def verify(window):
    '''检查两个扩展类是否分别生成了预期的布局容器和子控件。'''
    outer = window.layout()
    assert outer is not None and outer.count() == 4

    horizontal_layout = outer.itemAt(1).layout()
    vertical_layout = outer.itemAt(3).layout()

    assert isinstance(horizontal_layout, QHBoxLayout)
    assert isinstance(vertical_layout, QVBoxLayout)
    assert horizontal_layout.count() == 2
    assert vertical_layout.count() == 2

    horizontal_texts = [horizontal_layout.itemAt(i).widget().text() for i in range(2)]
    vertical_texts = [vertical_layout.itemAt(i).widget().text() for i in range(2)]
    assert horizontal_texts == ['H1', 'H2']
    assert vertical_texts == ['V1', 'V2']


def main():
    app, window = build()
    verify(window)
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
