# coding: utf-8
import unittest

from parsing import Parser, make_tree


SAMPLE_ROW = '''
<tr class="tCenter hl-tr">
    <td class="row4 med tLeft t-title"><div class="wbr t-title"><a data-topic_id="123456">Test title</a></div></td>
    <td class="row4 small nowrap tor-size"><u>234567</u></a></td>
    <td class="row4 small nowrap"><u>1455877521</u></td>
</tr>
'''


class ParserTestCase(unittest.TestCase):

    def test_parse_index_table_returns_all_rows(self):
        row = '<tr class="tCenter hl-tr"></tr>'
        html = '<table id="tor-tbl">' + row * 10 + '</table>'
        p = Parser()

        rows = p.parse_index_table(html)

        self.assertEqual(len(rows), 10)

    def test_parse_index_row_returns_dict(self):
        p = Parser()
        elem = make_tree(SAMPLE_ROW)

        result = p.parse_index_row(elem)

        self.assertEqual(type(result), dict)

    def test_index_tid_returns_tid(self):
        p = Parser()
        html = '<td class="t-title"><div class="t-title"><a data-topic_id="12345"></a></div></td>'
        tid = p.index_tid(make_tree(html))

        self.assertEqual(tid, 12345)

    def test_index_title_returns_title(self):
        p = Parser()
        html = '<td class="t-title"><div class="t-title"><a>Blah</a></div></td>'
        tid = p.index_title(make_tree(html))

        self.assertEqual(tid, 'Blah')

    def test_index_timestamp_returns_timestamp(self):
        p = Parser()
        html = '<tr><td></td><td><u>123456</u></td></tr>'
        ts = p.index_timestamp(make_tree(html))

        self.assertEqual(ts, 123456)

    def test_index_nbytes_returns_nbytes(self):
        p = Parser()
        html = '<td class="tor-size"><u>123456</u></td>'
        nbytes = p.index_nbytes(make_tree(html))

        self.assertEqual(nbytes, 123456)
