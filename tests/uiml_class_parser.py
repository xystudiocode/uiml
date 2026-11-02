'''UIMLLayout Parser API 的 GUI 演示。

文件名故意不带 test_ 前缀：该文件会打开窗口并进入 Qt 事件循环，
被 pytest 收集会导致测试挂起。运行方式：

    python tests/uiml_class_parser.py
'''
import uiml
from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget


uimlcode = '''
<layout name="root" direction="v">
    <QLabel name="title" args=['UIMLLayout Parser API demo'] />
    <layout name="row" direction="t">
        <QLabel name="left" args=['left'] />
        <QLabel name="right" args=['right'] />
    </layout>
</layout>
'''


class MyUIMLLayout(uiml.UIMLLayout):
    '''通过 Parser API 注册的自定义渲染类，无需修改调用点。'''

    def extend_layout(self, list_info):
        # 自定义布局方向 't'：把子项水平排列
        if str(list_info.get('direction', '')).lower() == 't':
            layout = QHBoxLayout()
            self._for_loop(list_info, layout)
            return layout, 'layout'
        return super().extend_layout(list_info)


def build():
    '''构建界面但不进入事件循环，方便做无窗口的 smoke test。'''
    app = QApplication.instance() or QApplication([])

    uiml.add_parser(uiml.ParserEnum.uiml_class, uiml.ControlEnum.reset)
    uiml.add_parser(uiml.ParserEnum.uiml_class, MyUIMLLayout)

    data = uiml.compile_ui(uiml.xml_parse(uimlcode))

    window = QWidget()
    window.setWindowTitle('UIMLLayout Parser API demo')
    window.setLayout(uiml.UIMLLayout(data).show())
    return app, window


def main():
    app, window = build()
    window.show()
    app.exec()


if __name__ == '__main__':
    main()
