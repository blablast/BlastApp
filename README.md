
# BlastApp – Aplikacja rozwiązywania wyrażeń logicznych (Logika Binarna)

## Opis projektu

**BlastApp** to interaktywna aplikacja GUI (oparta na frameworku [Streamlit](https://streamlit.io/)) służąca do rozwiązywania i analizowania zdań logicznych przy użyciu koncepcji **Logiki Binarnej**. Zaimplementowano dwa silniki: algebraiczny **OTA Solver** i bitowy **BlastSolver**, umożliwiające ultraszybkie znajdowanie *wszystkich* rozwiązań zadanych formuł logicznych. Aplikacja pozwala na wizualizację drzew logicznych, obliczenie funkcji OTA oraz prezentację wyników – bez potrzeby konstruowania tradycyjnych tabel prawdy.

---

## Wprowadzenie – Logika Binarna

**Logika Binarna** łączy klasyczną algebrę boolowską (gdzie 1 = PRAWDA, 0 = FAŁSZ) z tzw. algebrą binarną, wykorzystującą funkcję OTA do opisu rozwiązań. Innowacją jest traktowanie 0 i 1 jako liczb całkowitych, a nie symboli.

### Zalety:

- **Brak tabel prawdy** – wszystkie kombinacje wyznacza się za pomocą funkcji OTA, jednorazowo.
- **Brak konieczności znajomości praw logiki** – operacje logiczne tłumaczy się na działania algebraiczne.
- **Szybkość** – złożone zdania (np. z 20 zmiennymi) rozwiązywane są w ułamku sekundy.

**Funkcja OTA** (One-hot Truth Assignment) zapisuje wynik dla wszystkich kombinacji n zmiennych jako ciąg $2^n$ współczynników $t_i$. Przykład dla 2 zmiennych:  
$\Phi = t_3\cdot a_1 a_0 + t_2\cdot a_1 + t_1\cdot a_0 + t_0$

---

## Instalacja i uruchomienie

Aplikację uruchomisz na **Windows**, **Linux** lub **macOS**.

### Wymagania:

- Python 3.10+
- pip
- (opcjonalnie) wirtualne środowisko, np. `venv` lub `conda`

### Instalacja:

1. Rozpakuj archiwum `BlastApp.zip`.
2. W terminalu przejdź do katalogu z projektem.
3. Zainstaluj zależności:
    ```bash
    pip install -r requirements.txt
    ```
   **Uwaga:**  
   Jeśli korzystasz z Windows/macOS, zainstaluj również narzędzie **Graphviz** i dodaj do PATH (instrukcja na [graphviz.org](https://graphviz.org/download/)).

### Uruchomienie:

W folderze projektu wpisz:
```bash
    streamlit run app.py
```
Po chwili w przeglądarce otworzy się strona aplikacji (domyślnie: http://localhost:8501).

---

## Przykład działania

Załóżmy wyrażenie:
(a0 AND a1) OR (a1 AND a2) OR (a2 AND a0)

Dla 3 zmiennych aplikacja automatycznie:

- Wyświetli **drzewo logiczne**:

  ![Drzewo logiczne](img/screenshot_tree.png)

- Obliczy **funkcję OTA** oraz współczynniki dla wszystkich kombinacji:

  ![Tabela OTA](img/screenshot_ota.png)

- Pokaże **tabele wyników**:

  ![Wyniki](img/screenshot_results.png)

- Porówna czasy działania solverów (OTA/Blast):

  ![Porównanie solverów](img/screenshot_timing.png)

---

## Autor

**Błażej Strus**  
  e-mail: b.strus@gmail.com  
  tel: +48 501 165 889

---

## Licencja

Brak określonej licencji. Jeśli chcesz użyć kodu – skontaktuj się z autorem.

---
