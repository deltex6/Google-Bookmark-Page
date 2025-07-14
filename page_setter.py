import re
import os
import webbrowser
from pathlib import Path
from colorama import init, Fore, Style
import time

# Inicjalizacja colorama dla Windows
init()

def print_header():
    print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}║{Style.RESET_ALL}{'Google Bookmarks Export Beautifier':^58}{Fore.CYAN}║{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

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

def get_file_paths():
    print_header()
    
    # Plik wejściowy (pełna ścieżka)
    print(f"\n{Fore.CYAN}[1/2]{Style.RESET_ALL} Plik wejściowy")
    while True:
        input_path = get_input_with_prompt("Podaj pełną ścieżkę do pliku wejściowego:", required=True)
        if os.path.isfile(input_path):
            break
        print(f"{Fore.RED}✗ Podana ścieżka nie jest poprawnym plikiem!{Style.RESET_ALL}")
    
    # Plik wyjściowy
    print(f"\n{Fore.CYAN}[2/2]{Style.RESET_ALL} Plik wyjściowy")
    folder_path = os.path.dirname(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    default_output = f"{base_name}_new.html"
    
    output_file = get_input_with_prompt(
        "Podaj nazwę pliku wyjściowego:", 
        default=default_output
    )
    if not output_file:
        output_file = default_output
    
    # Tworzenie ścieżki wyjściowej
    output_path = os.path.join(folder_path, output_file)
    
    # Sprawdzenie czy plik wejściowy istnieje
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Nie znaleziono pliku wejściowego: {input_path}")
    
    return input_path, output_path

# Zakres linii do zamiany (1-indeksowane)
start_line = 1  # Rozpocznij od pierwszej linii
end_line = float('inf')  # Przetwarzaj do końca pliku

def get_base_html_template():
    return '''<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  
  <style>
  .main-title {
    font-size: 3em;
    text-align: center;
    margin: 1rem 0 2rem 0;
    color: #ce9178;
  }
  
  body {
    background-color: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Segoe UI', system-ui, sans-serif;
    line-height: 1.6;
    margin: 0;
    padding: 2rem;
  }

  dl {
    margin-left: 2rem;
    border-left: 1px solid #404040;
    padding-left: 1rem;
  }

  /* Pierwszy poziom dl nie ma wcięcia */
  body > dl {
    margin-left: 0;
    border-left: none;
    padding-left: 0;
  }

  dt {
    margin: 0.8rem 0;
  }

  a {
    color: #569cd6;
    text-decoration: none;
    transition: color 0.2s;
  }

  a:hover {
    color: #9cdcfe;
    text-decoration: underline;
  }

  h1, h2, h3, h4, h5, h6 {
    color: #ce9178;
    margin: 0.5rem 0;
    font-weight: 600;
  }

  h1 { font-size: 2.5em; }
  h2 { font-size: 2.2em; }
  h3 { font-size: 1.9em; }
  h4 { font-size: 1.6em; }
  h5 { font-size: 1.3em; }
  h6 { font-size: 1.1em; }
  </style>

  <script>
  document.addEventListener('DOMContentLoaded', function(){
    document.querySelectorAll('dt > h3').forEach(function(h){
      // policz głębokość – ile razy wspinamy się do rodzica <dl>
      let lvl = 1, el = h.parentElement;
      while (el = el.parentElement) {
        if (el.tagName.toLowerCase() === 'dl') lvl++;
      }
      
      // wybierz tag (maks. h6)
      const tag = 'h' + Math.min(lvl+1, 6);

      // stwórz nowy nagłówek
      const nh = document.createElement(tag);
      // przenieś atrybuty
      Array.from(h.attributes).forEach(a => nh.setAttribute(a.name, a.value));
      nh.innerHTML = h.innerHTML;
      // zastąp
      h.parentNode.replaceChild(nh, h);
    });
  });
  </script>
</head>
<body>
  <h1 class="main-title">TEST</h1>
'''

def add_html_structure(lines):
    # Usuwa stare meta, title i head jeśli istnieją
    i = 0
    while i < len(lines):
        if any(tag in lines[i].lower() for tag in ['<meta', '<title', '<head']):
            lines.pop(i)
        else:
            i += 1
    
    # Wstawia nową strukturę
    lines.insert(0, get_base_html_template() + '\n')

def remove_empty_dl(lines):
    i = 0
    while i < len(lines):
        line = lines[i].lower().strip()
        
        # Jeśli znaleźliśmy otwarcie dl
        if line == '<dl><p>':
            # Szukaj następnej niepustej linii
            next_i = i + 1
            while next_i < len(lines) and lines[next_i].strip() == '':
                next_i += 1
                
            # Jeśli następna niepusta linia to zamykający </dl><p>, usuń obie linie
            if next_i < len(lines) and lines[next_i].lower().strip() == '</dl><p>':
                # Usuń wszystkie linie między dl i /dl, włącznie z nimi
                for _ in range(next_i - i + 1):
                    lines.pop(i)
                continue
        
        # Usuń puste znaczniki <p>
        if line == '<p>' or line == '</p>':
            lines.pop(i)
            continue
            
        i += 1
    return lines

def lowercase_tags_in_range(input_path, output_path, start_line, end_line):
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Usuń stare linie nagłówka
    lines_to_remove = [
        '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
        '<!-- This is an automatically generated file.',
        '     It will be read and overwritten.',
        '     DO NOT EDIT! -->'
    ]
    
    # Usuń nagłówek
    i = 0
    while i < len(lines):
        if any(line.strip() in lines[i].strip() for line in lines_to_remove):
            lines.pop(i)
        else:
            i += 1
    
    # Usuń automatycznie generowany nagłówek H1 'Bookmarks'
    i = 0
    while i < len(lines):
        if re.search(r'<h1[^>]*>Bookmarks</h1>', lines[i], re.IGNORECASE):
            lines.pop(i)
        else:
            i += 1

    def lowercase_tags(line):
        # Zamienia tylko NAZWY znaczników na małe litery, atrybuty i treść zostawia
        def repl(m):
            tag = m.group(1).lower()
            rest = m.group(2)
            return f'<{tag}{rest}'
        # Otwierające i zamykające znaczniki
        line = re.sub(r'<(/?)([A-Z0-9\-]+)([^>]*)>', lambda m: f'<{m.group(1)}{m.group(2).lower()}{m.group(3)}>', line)
        return line

    max_idx = len(lines)
    for i in range(start_line-1, min(end_line, max_idx)):
        lines[i] = lowercase_tags(lines[i])

    # Usuń puste elementy dl
    lines = remove_empty_dl(lines)

    # Usuń puste linie na końcu pliku
    while lines and lines[-1].strip() == '':
        lines.pop()
        
    # Usuwa stare zamykające znaczniki body i html jeśli istnieją
    while lines and ('</body>' in lines[-1].lower() or '</html>' in lines[-1].lower()):
        lines.pop()

    # Dodaje zamykające znaczniki na końcu
    if lines and lines[-1].strip() != '':
        lines.append('\n')
    lines.append('</body>\n')
    lines.append('</html>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

if __name__ == "__main__":
    try:
        # Pobierz ścieżki od użytkownika
        input_path, output_path = get_file_paths()
        
        print(f"\n{Fore.CYAN}[Przetwarzanie]{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}►{Style.RESET_ALL} Konwertowanie znaczników na małe litery...")
        
        # Wykonaj konwersję
        lowercase_tags_in_range(input_path, output_path, start_line, end_line)
        print(f"{Fore.GREEN}✓ Znaczniki zostały przekonwertowane{Style.RESET_ALL}")
        
        print(f"{Fore.YELLOW}►{Style.RESET_ALL} Dodawanie struktury HTML...")
        # Dodanie struktury HTML
        with open(output_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        add_html_structure(lines)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print(f"{Fore.GREEN}✓ Struktura HTML została dodana{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}Gotowe!{Style.RESET_ALL}")
        print(f"Wynik zapisano do: {Fore.CYAN}{output_path}{Style.RESET_ALL}")
        
        # Otwórz plik w domyślnej przeglądarce
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
