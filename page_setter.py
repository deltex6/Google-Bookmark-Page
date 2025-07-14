import re
import os
import webbrowser
from pathlib import Path
from colorama import init, Fore, Style

# Inicjalizacja colorama dla Windows
init()

class BookmarkConverter:
    def __init__(self):
        self.header_lines_to_remove = [
            '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
            '<!-- This is an automatically generated file.',
            '     It will be read and overwritten.',
            '     DO NOT EDIT! -->'
        ]
    
    def convert_file(self, input_path, output_path):
        """Główna metoda konwertująca plik zakładek"""
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Kolejne etapy przetwarzania
        lines = self._remove_header_lines(lines)
        lines = self._remove_bookmarks_title(lines)
        lines = self._convert_tags_to_lowercase(lines)
        lines = self._remove_empty_elements(lines)
        lines = self._cleanup_and_add_html_structure(lines)
        
        # Zapisz wynik
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
    
    def _remove_header_lines(self, lines):
        """Usuwa linie nagłówka specyficzne dla formatu Netscape"""
        return [line for line in lines 
                if not ('<!DOCTYPE NETSCAPE-Bookmark-file-1>' in line
                    or '<!-- This is an automatically generated file.' in line
                    or 'It will be read and overwritten.' in line
                    or 'DO NOT EDIT! -->' in line)]
    
    def _remove_bookmarks_title(self, lines):
        """Usuwa domyślny nagłówek 'Bookmarks'"""
        return [line for line in lines 
                if not re.search(r'<h1[^>]*>Bookmarks</h1>', line, re.IGNORECASE)]
    
    def _convert_tags_to_lowercase(self, lines):
        """Konwertuje nazwy tagów HTML na małe litery"""
        def convert_line(line):
            return re.sub(r'<(/?)([A-Z0-9\-]+)([^>]*)>', 
                         lambda m: f'<{m.group(1)}{m.group(2).lower()}{m.group(3)}>', 
                         line)
        return [convert_line(line) for line in lines]
    
    def _remove_empty_elements(self, lines):
        """Usuwa puste elementy dl i znaczniki p"""
        result = []
        i = 0
        while i < len(lines):
            line = lines[i].lower().strip()
            
            if line == '<dl><p>':
                next_i = i + 1
                while next_i < len(lines) and not lines[next_i].strip():
                    next_i += 1
                    
                if next_i < len(lines) and lines[next_i].lower().strip() == '</dl><p>':
                    i = next_i + 1
                    continue
                    
            if line not in ['<p>', '</p>']:
                result.append(lines[i])
            i += 1
            
        return result
    
    def _cleanup_and_add_html_structure(self, lines):
        """Czyści i dodaje podstawową strukturę HTML"""
        # Usuń puste linie na końcu
        while lines and not lines[-1].strip():
            lines.pop()
            
        # Usuń stare znaczniki zamykające
        while lines and ('</body>' in lines[-1].lower() or '</html>' in lines[-1].lower()):
            lines.pop()
        
        # Dodaj nową strukturę HTML
        lines.insert(0, self._get_html_template())
        
        # Dodaj znaczniki zamykające
        if lines and lines[-1].strip():
            lines.append('\n')
        lines.append('</body>\n')
        lines.append('</html>')
        
        return lines
    
    def _get_html_template(self):
        """Zwraca szablon HTML z stylami i skryptami"""
        return '''<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  <style>
    .main-title { font-size: 3em; text-align: center; margin: 1rem 0 2rem 0; color: #ce9178; }
    body { background-color: #1e1e1e; color: #d4d4d4; font-family: 'Segoe UI', system-ui, sans-serif;
           line-height: 1.6; margin: 0; padding: 2rem; }
    dl { margin-left: 2rem; border-left: 1px solid #404040; padding-left: 1rem; }
    body > dl { margin-left: 0; border-left: none; padding-left: 0; }
    dt { margin: 0.8rem 0; }
    a { color: #569cd6; text-decoration: none; transition: color 0.2s; }
    a:hover { color: #9cdcfe; text-decoration: underline; }
    h1, h2, h3, h4, h5, h6 { color: #ce9178; margin: 0.5rem 0; font-weight: 600; }
    h1 { font-size: 2.5em; } h2 { font-size: 2.2em; } h3 { font-size: 1.9em; }
    h4 { font-size: 1.6em; } h5 { font-size: 1.3em; } h6 { font-size: 1.1em; }
  </style>
  <script>
    document.addEventListener('DOMContentLoaded', function(){
      document.querySelectorAll('dt > h3').forEach(function(h){
        let lvl = 1, el = h.parentElement;
        while (el = el.parentElement) {
          if (el.tagName.toLowerCase() === 'dl') lvl++;
        }
        const tag = 'h' + Math.min(lvl+1, 6);
        const nh = document.createElement(tag);
        Array.from(h.attributes).forEach(a => nh.setAttribute(a.name, a.value));
        nh.innerHTML = h.innerHTML;
        h.parentNode.replaceChild(nh, h);
      });
    });
  </script>
</head>
<body>
  <h1 class="main-title">TEST</h1>
'''

class CLI:
    @staticmethod
    def print_header():
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}║{Style.RESET_ALL}{'Google Bookmarks Export Beautifier':^58}{Fore.CYAN}║{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
    
    @staticmethod
    def get_input_with_prompt(prompt, required=False, default=None):
        while True:
            print(f"{Fore.YELLOW}►{Style.RESET_ALL} {prompt}")
            if default:
                print(f"{Fore.LIGHTBLACK_EX}  Domyślnie: {default}{Style.RESET_ALL}")
            value = input(f"{Fore.GREEN}❯{Style.RESET_ALL} ").strip()
            
            if not value:
                if required:
                    print(f"{Fore.RED}✗ To pole jest wymagane!{Style.RESET_ALL}")
                    continue
                return default
            return value
    
    @staticmethod
    def get_file_paths():
        CLI.print_header()
        
        print(f"\n{Fore.CYAN}[1/2]{Style.RESET_ALL} Plik wejściowy")
        while True:
            input_path = CLI.get_input_with_prompt("Podaj pełną ścieżkę do pliku wejściowego:", required=True)
            if os.path.isfile(input_path):
                break
            print(f"{Fore.RED}✗ Podana ścieżka nie jest poprawnym plikiem!{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}[2/2]{Style.RESET_ALL} Plik wyjściowy")
        folder_path = os.path.dirname(input_path)
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        default_output = f"{base_name}_new.html"
        
        output_file = CLI.get_input_with_prompt("Podaj nazwę pliku wyjściowego:", default=default_output)
        output_path = os.path.join(folder_path, output_file or default_output)
        
        return input_path, output_path
    
    @staticmethod
    def run():
        try:
            input_path, output_path = CLI.get_file_paths()
            
            print(f"\n{Fore.CYAN}[Przetwarzanie]{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}►{Style.RESET_ALL} Konwertowanie pliku...")
            
            converter = BookmarkConverter()
            converter.convert_file(input_path, output_path)
            
            print(f"{Fore.GREEN}✓ Plik został przekonwertowany{Style.RESET_ALL}")
            print(f"\n{Fore.GREEN}Gotowe!{Style.RESET_ALL}")
            print(f"Wynik zapisano do: {Fore.CYAN}{output_path}{Style.RESET_ALL}")
            
            try:
                print(f"\n{Fore.YELLOW}►{Style.RESET_ALL} Otwieranie pliku w przeglądarce...")
                webbrowser.open('file://' + os.path.abspath(output_path))
                print(f"{Fore.GREEN}✓ Plik został otwarty{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}✗ Nie udało się otworzyć pliku: {e}{Style.RESET_ALL}")
            
        except FileNotFoundError as e:
            print(f"\n{Fore.RED}✗ Błąd: {e}{Style.RESET_ALL}")
        except Exception as e:
            print(f"\n{Fore.RED}✗ Wystąpił nieoczekiwany błąd: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    CLI.run()
