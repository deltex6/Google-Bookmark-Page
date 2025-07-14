import unittest
import os
import sys
import tempfile
from pathlib import Path

# Dodaj ścieżkę do katalogu nadrzędnego, aby zaimportować moduł
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lowercase_html_tags import BookmarkConverter

class TestBookmarkConverter(unittest.TestCase):
    def setUp(self):
        """Przygotowanie środowiska testowego przed każdym testem"""
        self.converter = BookmarkConverter()
        self.temp_dir = tempfile.mkdtemp()
        self.sample_input = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<!-- This is an automatically generated file.
     It will be read and overwritten.
     DO NOT EDIT! -->
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
    <DT><H3 ADD_DATE="1664625840" LAST_MODIFIED="1748005646">Test Folder</H3>
    <DL><p>
        <DT><A HREF="https://example.com">Example Link</A>
    </DL><p>
</DL><p>'''

    def tearDown(self):
        """Czyszczenie po każdym teście"""
        for file in Path(self.temp_dir).glob("*"):
            file.unlink()
        os.rmdir(self.temp_dir)

    def test_remove_header_lines(self):
        """Test usuwania linii nagłówka"""
        lines = self.sample_input.split('\n')
        result = self.converter._remove_header_lines(lines)
        
        # Sprawdź czy usunięto nagłówki
        self.assertFalse(any('DOCTYPE NETSCAPE' in line for line in result))
        self.assertFalse(any('automatically generated' in line for line in result))
        self.assertFalse(any('DO NOT EDIT' in line for line in result))

    def test_remove_bookmarks_title(self):
        """Test usuwania tytułu 'Bookmarks'"""
        lines = ['<H1>Bookmarks</H1>', '<DL><p>', '<DT><A HREF="#">Link</A></DL><p>']
        result = self.converter._remove_bookmarks_title(lines)
        
        # Sprawdź czy usunięto tytuł Bookmarks
        self.assertFalse(any('<h1>Bookmarks</h1>' in line.lower() for line in result))
        self.assertTrue(any('<dl><p>' in line.lower() for line in result))

    def test_convert_tags_to_lowercase(self):
        """Test konwersji tagów na małe litery"""
        lines = ['<DL><p>', '<DT><A HREF="#">Link</A></DL><p>']
        result = self.converter._convert_tags_to_lowercase(lines)
        
        # Sprawdź czy nazwy tagów są małymi literami, ale atrybuty i treść pozostają bez zmian
        self.assertEqual('<dl><p>', result[0])
        self.assertEqual('<dt><a HREF="#">Link</a></dl><p>', result[1])
        
        # Dodatkowe sprawdzenie dla bardziej złożonego przypadku
        complex_line = '<DT><H3 ADD_DATE="123" LAST_MODIFIED="456">Test Folder</H3></DT>'
        result_complex = self.converter._convert_tags_to_lowercase([complex_line])[0]
        
        # Sprawdź czy:
        # - nazwy tagów (DT, H3) zostały zamienione na małe litery
        # - atrybuty (ADD_DATE, LAST_MODIFIED) pozostały niezmienione
        # - treść (Test Folder) pozostała niezmieniona
        self.assertEqual(
            '<dt><h3 ADD_DATE="123" LAST_MODIFIED="456">Test Folder</h3></dt>',
            result_complex)

    def test_remove_empty_elements(self):
        """Test usuwania pustych elementów"""
        lines = [
            '<dl><p>',
            '</dl><p>',
            '<dl><p>',
            '    <dt><a href="#">Link</a></dt>',
            '</dl><p>'
        ]
        result = self.converter._remove_empty_elements(lines)
        
        # Sprawdź czy usunięto pusty element dl
        self.assertTrue(len(result) < len(lines))
        self.assertTrue(any('Link' in line for line in result))

    def test_full_conversion(self):
        """Test pełnej konwersji pliku"""
        # Utwórz tymczasowe pliki
        input_path = os.path.join(self.temp_dir, "test_input.html")
        output_path = os.path.join(self.temp_dir, "test_output.html")
        
        # Zapisz przykładowe dane wejściowe
        with open(input_path, 'w', encoding='utf-8') as f:
            f.write(self.sample_input)
        
        # Wykonaj konwersję
        self.converter.convert_file(input_path, output_path)
        
        # Sprawdź czy plik wyjściowy istnieje i ma odpowiednią zawartość
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            # Sprawdź czy zawiera wymagane elementy
            self.assertTrue('<!doctype html>' in content)
            self.assertTrue('<html>' in content)
            self.assertTrue('<head>' in content)
            self.assertTrue('<body>' in content)
            self.assertTrue('</html>' in content)
            # Sprawdź czy nie zawiera starych nagłówków
            self.assertFalse('netscape-bookmark-file' in content)
            self.assertFalse('do not edit' in content)

if __name__ == '__main__':
    unittest.main()
