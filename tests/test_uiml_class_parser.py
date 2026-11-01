import pytest

import uiml


DATA = {'name': 'root', 'direction': 'v', 'content': []}


class CustomLayout(uiml.UIMLLayout):
    init_count = 0

    def __init__(self, list):
        super().__init__(list)
        type(self).init_count += 1


@pytest.fixture(autouse=True)
def reset_uiml_class_chain():
    '''每个用例前后都恢复默认的 UI 类解析器，避免用例互相污染。'''
    uiml.add_parser(uiml.ParserEnum.uiml_class, uiml.ControlEnum.reset)
    CustomLayout.init_count = 0
    yield
    uiml.add_parser(uiml.ParserEnum.uiml_class, uiml.ControlEnum.reset)


def test_register_class_returns_custom_layout():
    uiml.add_parser(uiml.ParserEnum.uiml_class, CustomLayout)

    layout = uiml.UIMLLayout(DATA)

    assert isinstance(layout, CustomLayout)
    assert layout.list is DATA
    # 元类只构造一次，不能因为全局解析器再执行一遍 __init__
    assert CustomLayout.init_count == 1


def test_register_factory_and_fallthrough():
    def factory(data):
        return CustomLayout(data)

    uiml.add_parser(uiml.ParserEnum.uiml_class, factory)
    assert isinstance(uiml.UIMLLayout(DATA), CustomLayout)

    # 后注册的解析器先执行；返回 None 时回退到先注册的 factory
    uiml.add_parser(uiml.ParserEnum.uiml_class, lambda data: None)
    assert isinstance(uiml.UIMLLayout(DATA), CustomLayout)


def test_reset_restores_default_layout():
    uiml.add_parser(uiml.ParserEnum.uiml_class, CustomLayout)
    assert isinstance(uiml.UIMLLayout(DATA), CustomLayout)

    uiml.add_parser(uiml.ParserEnum.uiml_class, uiml.ControlEnum.reset)

    assert type(uiml.UIMLLayout(DATA)) is uiml.UIMLLayout
    assert uiml.uiml_class_chain.funcs == uiml.uiml_class_chain._default_funcs
    # reset 后不能和默认列表共享同一个列表对象，否则后续 add 会污染默认值
    assert uiml.uiml_class_chain.funcs is not uiml.uiml_class_chain._default_funcs


def test_explicit_subclass_is_not_replaced():
    class OtherLayout(uiml.UIMLLayout):
        pass

    uiml.add_parser(uiml.ParserEnum.uiml_class, OtherLayout)

    layout = CustomLayout(DATA)

    assert type(layout) is CustomLayout
    assert not isinstance(layout, OtherLayout)


def test_invalid_parser_result_raises_type_error():
    uiml.add_parser(uiml.ParserEnum.uiml_class, lambda data: object())

    with pytest.raises(TypeError, match='UIMLLayout'):
        uiml.UIMLLayout(DATA)


def test_parser_can_construct_base_layout_recursively():
    def factory(data):
        base = uiml.UIMLLayout(data)  # 递归保护：这里必须得到基类实例
        assert type(base) is uiml.UIMLLayout
        return CustomLayout(data)

    uiml.add_parser(uiml.ParserEnum.uiml_class, factory)

    assert isinstance(uiml.UIMLLayout(DATA), CustomLayout)


def test_registered_layout_keeps_extension_hooks():
    class HookedLayout(uiml.UIMLLayout):
        def extend_layout(self, list_info):
            return 'hooked', 'layout'

    uiml.add_parser(uiml.ParserEnum.uiml_class, HookedLayout)

    layout = uiml.UIMLLayout(DATA)

    assert layout.extend_layout({'direction': 't'}) == ('hooked', 'layout')

    uiml.add_parser(uiml.ParserEnum.uiml_class, uiml.ControlEnum.reset)
    with pytest.raises(uiml.UIMLException):
        uiml.UIMLLayout(DATA).extend_layout({'direction': 't'})


def test_missing_data_still_raises_type_error():
    with pytest.raises(TypeError):
        uiml.UIMLLayout()


class MultiHorizontalLayout(uiml.UIMLLayout):
    marker = 'horizontal'


class MultiVerticalLayout(uiml.UIMLLayout):
    marker = 'vertical'


def make_horizontal_layout(data):
    if str(data.get('direction', '')).lower() == 'x':
        return MultiHorizontalLayout(data)
    return None


def make_vertical_layout(data):
    if str(data.get('direction', '')).lower() == 'y':
        return MultiVerticalLayout(data)
    return None


def test_multiple_extensions_dispatch_by_direction():
    '''同时注册两个扩展类时，各自按布局方向接管自己的数据。'''
    uiml.add_parser(uiml.ParserEnum.uiml_class, make_horizontal_layout)
    uiml.add_parser(uiml.ParserEnum.uiml_class, make_vertical_layout)

    horizontal = uiml.UIMLLayout({'name': 'root', 'direction': 'x', 'content': []})
    vertical = uiml.UIMLLayout({'name': 'root', 'direction': 'y', 'content': []})
    fallback = uiml.UIMLLayout({'name': 'root', 'direction': 'v', 'content': []})

    assert type(horizontal) is MultiHorizontalLayout
    assert type(vertical) is MultiVerticalLayout
    # 两个扩展都不接管的布局方向仍然回退到默认 UIMLLayout
    assert type(fallback) is uiml.UIMLLayout


def test_multiple_extensions_registration_order_independent():
    '''注册顺序不应影响按方向分派的结果。'''
    uiml.add_parser(uiml.ParserEnum.uiml_class, make_vertical_layout)
    uiml.add_parser(uiml.ParserEnum.uiml_class, make_horizontal_layout)

    assert type(uiml.UIMLLayout({'name': 'root', 'direction': 'x', 'content': []})) is MultiHorizontalLayout
    assert type(uiml.UIMLLayout({'name': 'root', 'direction': 'y', 'content': []})) is MultiVerticalLayout


def test_multiple_extensions_reset_removes_all():
    uiml.add_parser(uiml.ParserEnum.uiml_class, make_horizontal_layout)
    uiml.add_parser(uiml.ParserEnum.uiml_class, make_vertical_layout)

    uiml.add_parser(uiml.ParserEnum.uiml_class, uiml.ControlEnum.reset)

    assert type(uiml.UIMLLayout({'name': 'root', 'direction': 'x', 'content': []})) is uiml.UIMLLayout
    assert type(uiml.UIMLLayout({'name': 'root', 'direction': 'y', 'content': []})) is uiml.UIMLLayout

