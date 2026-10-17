import uiml

xml_str = '''
<a.b c.d="123">
    <a_e>345</a_e>
</a.b>
'''

def test_main():
    assert uiml.xml_parse(xml_str) == {'type': 'a.b', 'c.d': '123', 'content': [{'type': 'a_e', 'content': '345'}]}

if __name__ == '__main__':
    test_main()