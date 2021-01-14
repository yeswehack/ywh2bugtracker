import unittest

from ywh2bt.tests.resource import resource
from ywh2bt.core.converter.jira2markdown import jira2markdown


class TestJira2Markdown(unittest.TestCase):

    def _convert_and_check(
        self,
        src: str,
        expected: str,
    ) -> None:
        actual = jira2markdown(
            src=src,
        )
        self.assertEqual(expected, actual)

    def test_convert_document(self) -> None:
        with open(resource('converter/jira/jira.jira')) as f:
            src = f.read()
        with open(resource('converter/jira/jira.md')) as f:
            expected = f.read()
        self._convert_and_check(
            src=src,
            expected=expected,
        )

    def test_convert_bold(self) -> None:
        self._convert_and_check(
            src='*bold*',
            expected='**bold**',
        )

    def test_convert_italic(self) -> None:
        self._convert_and_check(
            src='_italic_',
            expected='*italic*',
        )

    def test_convert_monospaced(self) -> None:
        self._convert_and_check(
            src='{{monospaced}}',
            expected='`monospaced`',
        )

    def test_convert_strikethrough(self) -> None:
        self._convert_and_check(
            src='-deleted-',
            expected='~~deleted~~',
        )

    def test_convert_inserts(self) -> None:
        self._convert_and_check(
            src='+inserted+',
            expected='<ins>inserted</ins>',
        )

    def test_convert_superscript(self) -> None:
        self._convert_and_check(
            src='^superscript^',
            expected='<sup>superscript</sup>',
        )

    def test_convert_subscript(self) -> None:
        self._convert_and_check(
            src='~subscript~',
            expected='<sub>subscript</sub>',
        )

    def test_convert_preformatted_blocks(self) -> None:
        self._convert_and_check(
            src='{code}\nso *no* further _formatting_ is done here\n{code}',
            expected='```\nso *no* further _formatting_ is done here\n```',
        )

    def test_convert_language_specific_code_blocks(self) -> None:
        self._convert_and_check(
            src="{code:javascript}\nvar hello = 'world';\n{code}",
            expected="```javascript\nvar hello = 'world';\n```",
        )

    def test_convert_code_without_language_specific_and_with_title_into_code_block(self) -> None:
        self._convert_and_check(
            src='{code:title=Foo.java}\nclass Foo {\n  public static void main() {\n  }\n}\n{code}',
            expected='```\nclass Foo {\n  public static void main() {\n  }\n}\n```',
        )

    def test_convert_fully_configured_code_block(self) -> None:
        self._convert_and_check(
            src='{code:xml|title=MyTitle|borderStyle=dashed|borderColor=#ccc|titleBGColor=#F7D6C1|bgColor=#FFFFCE}' +
                '\n    <test>' +
                '\n        <another tag="attribute"/>' +
                '\n    </test>' +
                '\n{code}',
            expected='```xml' + '\n    <test>' + '\n        <another tag="attribute"/>' + '\n    </test>' + '\n```',
        )

    def test_convert_simple_links(self) -> None:
        self._convert_and_check(
            src='[http://google.com]',
            expected='<http://google.com>',
        )

    def test_not_convert_brackets_content_that_looks_like_unnamed_links(self) -> None:
        self._convert_and_check(
            src='[this is really not a link]',
            expected='[this is really not a link]',
        )

    def test_convert_named_links(self) -> None:
        self._convert_and_check(
            src='[Google|http://google.com]',
            expected='[Google](http://google.com)',
        )

    def test_convert_headers(self) -> None:
        self._convert_and_check(
            src='h1. Biggest heading',
            expected='# Biggest heading',
        )
        self._convert_and_check(
            src='h2. Bigger heading',
            expected='## Bigger heading',
        )
        self._convert_and_check(
            src='h3. Big heading',
            expected='### Big heading',
        )
        self._convert_and_check(
            src='h4. Normal heading',
            expected='#### Normal heading',
        )
        self._convert_and_check(
            src='h5. Small heading',
            expected='##### Small heading',
        )
        self._convert_and_check(
            src='h6. Smallest heading',
            expected='###### Smallest heading',
        )

    def test_convert_blockquote(self) -> None:
        self._convert_and_check(
            src='bq. This is a long blockquote type thingy that needs to be converted.',
            expected='> This is a long blockquote type thingy that needs to be converted.',
        )

    def test_convert_quote_block(self) -> None:
        self._convert_and_check(
            src='{quote}\n' +
                'We\'d like to file this exemption for this issue  \n' +
                'SNECETQZUM-230 HDR-001-TC1: Black flash is observed when you enter and exit HDR playback when connected to Sony/LG/Vizio HDR TV\'s  \n' +
                'please help to review with the attached file\n' +
                '{quote}',
            expected='> We\'d like to file this exemption for this issue  \n' +
                     '> SNECETQZUM-230 HDR-001-TC1: Black flash is observed when you enter and exit HDR playback when connected to Sony/LG/Vizio HDR TV\'s  \n' +
                     '> please help to review with the attached file\n',
        )

    def test_convert_lists(self) -> None:
        self._convert_and_check(
            src='* Foo\n* Bar\n* Baz\n** FooBar\n** BarBaz\n*** FooBarBaz\n* Starting Over',
            expected='* Foo\n* Bar\n* Baz\n  * FooBar\n  * BarBaz\n    * FooBarBaz\n* Starting Over',
        )

    def test_convert_numbered_lists(self) -> None:
        self._convert_and_check(
            src='# Foo\n# Bar\n# Baz\n## FooBar\n## BarBaz\n### FooBarBaz\n# Starting Over',
            expected='1. Foo\n1. Bar\n1. Baz\n  1. FooBar\n  1. BarBaz\n    1. FooBarBaz\n1. Starting Over',
        )

    def test_convert_bold_italic_combined(self) -> None:
        self._convert_and_check(
            src='This is _*emphatically bold*_!',
            expected='This is ***emphatically bold***!',
        )

    def test_convert_bold_within_unordered_list(self) -> None:
        self._convert_and_check(
            src='* This is not bold!\n** This is *bold*.',
            expected='* This is not bold!\n  * This is **bold**.',
        )

    # def test_be able to handle a complicated multi-line jira-wiki string and convert it to markdown() -> None:
    # var jira_str = fs.readFileSync(path.resolve(__dirname, 'test.jira'), 'utf8');
    # var md_str = fs.readFileSync(path.resolve(__dirname, 'test.md'), 'utf8');
    # const markdown = j2m.toMarkdown(jira_str);
    # expect(markdown).toBe(md_str);
    # });
    def test_convert_special_tags_for_color_attributes(self) -> None:
        self._convert_and_check(
            src='A text with{color:blue} blue \n lines {color} is not necessary.',
            expected='A text with<span style="color:blue" class="text-color-blue"> blue \n lines </span> is not necessary.',
        )

    def test_convert_table_no_header(self) -> None:
        self._convert_and_check(
            src='| | | A | B |	C |\n' +
                '|Row 1|	Amarillo	|5.0	|2700|	25165824|\n' +
                '|Row 2|	Gilbert|	5.0|	2550|	25165824|\n' +
                '|Row 3|	Midland|	5.0|	2485|	33554432|\n' +
                '|Row 4|	Briscoe|	4.2|	4100|	67108864| \n' +
                '|Row 5|	Littlefield|	4.2|	3850|	67108864|\n' +
                '| | Row 6| |		4000| |	  \n' +
                '| | Row 7| |		3750| |\n',
            expected='| | | | | |\n' +
                     '| --- | --- | --- | --- | --- |\n' +
                     '| | | A | B |	C |\n' +
                     '|Row 1|	Amarillo	|5.0	|2700|	25165824|\n' +
                     '|Row 2|	Gilbert|	5.0|	2550|	25165824|\n' +
                     '|Row 3|	Midland|	5.0|	2485|	33554432|\n' +
                     '|Row 4|	Briscoe|	4.2|	4100|	67108864|\n' +
                     '|Row 5|	Littlefield|	4.2|	3850|	67108864|\n' +
                     '| | Row 6| |		4000| |\n' +
                     '| | Row 7| |		3750| |\n',
        )

    def test_convert_table(self) -> None:
        self._convert_and_check(
            src='||Heading 1||Heading 2||\n' +
                '|Col A1|Col A2|\n' +
                '|Col B1|Col B2|\n',
            expected='|Heading 1|Heading 2|\n' +
                     '| --- | --- |\n' +
                     '|Col A1|Col A2|\n' +
                     '|Col B1|Col B2|\n',
        )
