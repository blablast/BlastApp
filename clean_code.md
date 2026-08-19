# Dobre praktyki programowania - podstawy

**Autor:** Błażej Strus | **28 zasad** | **6 grup** | **Python**

---

## Grupa 1 - Nazewnictwo i czytelność

> Kod czyta się 10x częściej niż pisze. Te zasady sprawiają, że czytanie jest bezbolesne.

### 01. Znaczące nazwy

Nazwa zmiennej, funkcji czy klasy to pierwsza dokumentacja. Jeśli trzeba zajrzeć do ciała funkcji, żeby zrozumieć co robi - nazwa jest zła. Dobre nazwy eliminują potrzebę pisania komentarzy, przyspieszają code review i zmniejszają ryzyko błędów. Jeśli ktoś po przeczytaniu samej nazwy nie jest w stanie powiedzieć, za co odpowiada dany element - trzeba zmienić nazwę.

```python
# ŹLE - trzeba zgadywać
d = 7
def calc(a, b):
    return a * b

# DOBRZE - nazwa mówi wszystko
days_until_deadline = 7
def calculate_total_price(quantity, unit_price):
    return quantity * unit_price
```

### 02. Komentarze - kod powinien się sam tłumaczyć

Komentarz to najczęściej sygnał, że kod nie jest wystarczająco czytelny. Zamiast komentować - zmień nazwę, wydziel funkcję lub uprość warunek. Komentarze się dezaktualizują (kod się zmienia, komentarz zostaje), a nieaktualny komentarz jest gorszy niż jego brak. Wyjątki: komentarze prawne, wyjaśnienie intencji przy workaroundzie, ostrzeżenia o konsekwencjach, TODO z numerem taska.

Komentarze i docstringi piszemy po polsku, z pełnymi ogonkami (identyfikatory kodu zostają po angielsku). Wyjaśniają *dlaczego*, nie *co* - intencję, decyzję projektową, kompromis albo nieoczywiste ograniczenie; kod pokazuje, co robi. Bez narracji historycznej (changelogi, daty, "kiedyś zwracało nic", "backward compatible") - historię trzyma git, a powód opisujemy w czasie teraźniejszym. Bez odwołań do ticketów, commitów, nazwisk czy numerów linii - komentarz ma być samowystarczalny.

```python
# ŹLE - komentarz tłumaczy nieczytelny warunek
# sprawdź czy pracownik ma prawo do urlopu
if e.type == 1 and e.months > 6 and e.days_left > 0:
    ...

# DOBRZE - kod sam się tłumaczy
def is_eligible_for_vacation(employee):
    return (employee.is_full_time
            and employee.months_employed > 6
            and employee.vacation_days_left > 0)

if is_eligible_for_vacation(employee):
    ...
```

### 03. Jawność ponad domyślność (Explicit is better than Implicit)

Nie zmuszaj czytelnika kodu do domyślania się, co się dzieje. Jawne wywołania, jawne typy, jawne zależności - to fundament czytelności. Magiczne metody (`__getattr__`), automatyczne rejestracje i globalne stany wyglądają elegancko, ale utrudniają debugowanie, nawigację (IDE nie może znaleźć definicji) i zrozumienie przepływu danych.

```python
# ŹLE - magiczne przechwytywanie atrybutów
class Config:
    def __getattr__(self, name):
        return os.environ.get(name.upper(), "")

cfg = Config()
print(cfg.database_url)  # działa, ale IDE nie podpowie

# DOBRZE - jawna struktura, pełne wsparcie IDE
@dataclass
class Config:
    database_url: str
    debug: bool = False

    @classmethod
    def from_env(cls):
        return cls(
            database_url=os.environ["DATABASE_URL"],
            debug=os.environ.get("DEBUG", "false").lower() == "true",
        )
```

### 04. POLA - Zasada najmniejszego zaskoczenia (Principle of Least Astonishment)

Kod powinien zachowywać się **dokładnie tak**, jak sugerują jego nazwa, sygnatura i typ zwracany. Gdy programista widzi `get_total()`, oczekuje zapytania - odczytania wartości bez zmiany stanu. Konwencje: `is_` zwraca `bool`, `get_` nie modyfikuje stanu, `set_` nie zwraca wartości.

```python
# ŹLE - getter po cichu czyści koszyk
class ShoppingCart:
    def get_total(self):
        self.items = []  # <- dlaczego getter czyści koszyk?!
        return self._total

# DOBRZE - zachowanie zgodne z nazwą
class ShoppingCart:
    def get_total(self):
        return sum(item.price for item in self.items)

    def clear(self):
        self.items = []
```

---

## Grupa 2 - Funkcje i metody

> Funkcja to podstawowa jednostka kodu. Dobrze napisana - upraszcza system. Źle - go niszczy.

### 05. Funkcje powinny być małe i robić jedną rzecz

Funkcja powinna realizować **dokładnie jedno zadanie** na **jednym poziomie abstrakcji**. Gdy funkcja waliduje, przelicza i zapisuje naraz - staje się trudna do przetestowania i ponownego użycia. Jeśli potrafisz wydzielić fragment i nadać mu sensowną nazwę - oryginalna funkcja robiła za dużo.

```python
# ŹLE - walidacja, obliczenia, zapis i mail w jednym
def process_order(order):
    if not order.items:
        raise ValueError("Puste zamówienie")
    total = sum(i.price * i.qty for i in order.items)
    order.total = total
    db.save(order)
    send_email(order.customer, f"Zamówienie na {total} zł")

# DOBRZE - każda funkcja robi jedną rzecz
def validate_order(order):
    if not order.items:
        raise ValueError("Puste zamówienie")

def calculate_total(order):
    return sum(item.price * item.qty for item in order.items)

def process_order(order):
    validate_order(order)
    order.total = calculate_total(order)
    db.save(order)
    notify_customer(order)
```

### 06. Argumenty funkcji - im mniej, tym lepiej

Im więcej argumentów, tym trudniej zapamiętać kolejność i przetestować. Ideał to **zero**, dopuszczalne **jeden-dwa**. Trzy i więcej - to sygnał, że argumenty tworzą logiczną grupę i powinny być opakowane w obiekt (np. `dataclass`).

```python
# ŹLE - sześć luźnych argumentów
def create_user(name, email, age, city, role, active):
    ...

# DOBRZE - argumenty zgrupowane w obiekt
@dataclass
class UserData:
    name: str
    email: str
    age: int
    city: str
    role: str = "user"
    active: bool = True

def create_user(data: UserData):
    ...
```

### 07. Unikaj efektów ubocznych

Efekt uboczny (side effect) to każde działanie wykraczające poza to, co sugeruje nazwa funkcji - np. modyfikacja stanu globalnego, inicjalizacja sesji, wysłanie maila. Jeśli funkcja musi mieć efekt uboczny - niech nazwa o tym informuje.

```python
# ŹLE - "sprawdź hasło" inicjalizuje sesję
def check_password(user, password):
    if user.password == hash(password):
        Session.initialize()   # <- niespodzianka!
        return True
    return False

# DOBRZE - robi wyłącznie to, co obiecuje nazwa
def is_password_valid(user, password):
    return user.password_hash == hash(password)
```

### 08. CQS - Rozdzielenie poleceń i zapytań (Command-Query Separation)

Każda metoda powinna albo **zmieniać stan** (polecenie), albo **zwracać dane** (zapytanie) - nigdy jedno i drugie naraz. Zapytania są idempotentne (wielokrotne wywołanie daje ten sam wynik), polecenia jasno komunikują zmianę.

```python
# ŹLE - zmiana stanu + zwrot wartości
class Stack:
    def pop(self):
        return self.items.pop()

# DOBRZE - osobne metody
class Stack:
    def top(self):          # zapytanie - tylko odczyt
        return self.items[-1]

    def remove_top(self):   # polecenie - tylko zmiana stanu
        self.items.pop()
```

> W standardowej bibliotece `list.pop()` celowo łamie CQS dla wygody - to akceptowany kompromis. W kodzie domenowym staraj się rozdzielać.

### 09. Fail Fast / Klauzule strażnicze (Guard Clauses)

Waliduj dane wejściowe **na samym początku** funkcji i przerywaj natychmiast. Wzorzec guard clause eliminuje zagnieżdżone `if`-y - "ścieżka sukcesu" (happy path) jest płaska i czytelna na końcu.

```python
# ŹLE - głębokie zagnieżdżenie
def process_payment(order):
    if order:
        if order.items:
            if order.total > 0:
                if order.customer.has_payment_method:
                    charge(order)

# DOBRZE - guard clauses, happy path na końcu
def process_payment(order):
    if not order:
        raise ValueError("Brak zamówienia")
    if not order.items:
        raise ValueError("Puste zamówienie")
    if order.total <= 0:
        raise ValueError("Nieprawidłowa kwota")
    if not order.customer.has_payment_method:
        raise PaymentError("Brak metody płatności")

    charge(order)  # <- ścieżka sukcesu
```

---

## Grupa 3 - Zasady SOLID

> Pięć filarów projektowania obiektowego (R.C. Martin). Tworzą kod, który da się rozszerzać bez przepisywania.

### 10. S - Zasada jednej odpowiedzialności (Single Responsibility Principle - SRP)

Klasa powinna mieć **jeden i tylko jeden powód do zmiany**. Prosty test: opisz klasę jednym zdaniem bez słów "i", "oraz", "a także". Jeśli nie potrafisz - klasa robi za dużo.

```python
# ŹLE - trzy odpowiedzialności
class Employee:
    def calculate_pay(self): ...
    def save_to_database(self): ...
    def generate_report(self): ...

# DOBRZE - każda klasa = jedna odpowiedzialność
class Employee:
    def calculate_pay(self): ...

class EmployeeRepository:
    def save(self, employee): ...

class EmployeeReportGenerator:
    def generate(self, employee): ...
```

### 11. O - Zasada otwarte-zamknięte (Open/Closed Principle - OCP)

Moduł powinien być **otwarty na rozszerzanie**, ale **zamknięty na modyfikację**. Dodanie nowej funkcjonalności nie powinno wymagać zmiany istniejącego kodu. W praktyce osiąga się to przez polimorfizm: zamiast rozbudowywać `if/elif`, definiujesz nową klasę implementującą wspólny interfejs.

```python
# ŹLE - dodanie nowego kształtu wymaga modyfikacji istniejącej funkcji
def calculate_area(shape):
    if shape.type == "circle":
        return 3.14 * shape.radius ** 2
    elif shape.type == "rectangle":
        return shape.width * shape.height
    # <- każdy nowy kształt = modyfikacja tej funkcji

# DOBRZE - nowy kształt = nowa klasa, zero zmian w istniejącym kodzie
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self) -> float: ...

class Circle(Shape):
    def __init__(self, radius): self.radius = radius
    def area(self): return 3.14 * self.radius ** 2

class Rectangle(Shape):
    def __init__(self, w, h): self.w, self.h = w, h
    def area(self): return self.w * self.h

# Dodanie Triangle nie zmienia Circle ani Rectangle
```

### 12. L - Zasada podstawienia Liskov (Liskov Substitution Principle - LSP)

Obiekt klasy potomnej **musi dać się użyć wszędzie tam, gdzie oczekiwany jest obiekt klasy bazowej**, bez łamania poprawności programu. Jeśli podklasa łamie kontrakt - zmień hierarchię albo wydziel osobny interfejs.

```python
# ŹLE - podklasa łamie kontrakt klasy bazowej
class Bird:
    def fly(self): return "lecę"

class Penguin(Bird):
    def fly(self):
        raise NotImplementedError("Pingwiny nie latają")
        # <- każdy kod oczekujący Bird.fly() wybuchnie

# DOBRZE - osobne interfejsy dla osobnych zdolności
from abc import ABC, abstractmethod

class Bird(ABC):
    @abstractmethod
    def move(self): ...

class Sparrow(Bird):
    def move(self): return "lecę"

class Penguin(Bird):
    def move(self): return "chodzę"
    # <- oba spełniają kontrakt Bird.move()
```

### 13. I - Zasada segregacji interfejsów (Interface Segregation Principle - ISP)

Klient nie powinien być zmuszany do zależenia od metod, których nie używa. Jeden "gruby" interfejs z 10 metodami zmusza każdą implementację do dostarczenia wszystkich 10. Rozbij gruby interfejs na kilka małych, wyspecjalizowanych.

```python
# ŹLE - jeden gruby interfejs wymusza zbędne metody
class Worker(ABC):
    @abstractmethod
    def work(self): ...
    @abstractmethod
    def eat(self): ...
    @abstractmethod
    def sleep(self): ...

class Robot(Worker):
    def work(self): return "pracuję"
    def eat(self): raise NotImplementedError  # <- robot nie je!
    def sleep(self): raise NotImplementedError

# DOBRZE - małe, wyspecjalizowane interfejsy
class Workable(ABC):
    @abstractmethod
    def work(self): ...

class Feedable(ABC):
    @abstractmethod
    def eat(self): ...

class Human(Workable, Feedable):
    def work(self): return "pracuję"
    def eat(self): return "jem"

class Robot(Workable):  # <- implementuje tylko to, co potrzebne
    def work(self): return "pracuję"
```

### 14. D - Zasada odwrócenia zależności (Dependency Inversion Principle - DIP)

Moduły wysokopoziomowe (logika biznesowa) **nie powinny zależeć od modułów niskopoziomowych**. Oba powinny zależeć od abstrakcji. Dzięki temu możesz podmienić bazę danych, system plików lub API bez zmiany logiki biznesowej. To fundament testowalności - w testach wstrzykujesz mock zamiast prawdziwej bazy.

```python
# ŹLE - logika biznesowa zależy wprost od konkretnej bazy
class OrderService:
    def __init__(self):
        self.db = PostgresDatabase()  # <- twarda zależność

    def save_order(self, order):
        self.db.insert("orders", order.to_dict())

# DOBRZE - zależność od abstrakcji, wstrzykiwana z zewnątrz
class OrderRepository(ABC):
    @abstractmethod
    def save(self, order): ...

class PostgresOrderRepo(OrderRepository):
    def save(self, order):
        self.db.insert("orders", order.to_dict())

class OrderService:
    def __init__(self, repo: OrderRepository):
        self.repo = repo  # <- abstrakcja, nie konkret

    def save_order(self, order):
        self.repo.save(order)

# W testach: OrderService(FakeOrderRepo())
```

---

## Grupa 4 - Architektura i struktura

> Jak organizować klasy, moduły i pliki, żeby projekt nie zamienił się w labirynt.

### 15. Kompozycja ponad dziedziczenie (Composition over Inheritance)

Dziedziczenie tworzy **silne sprzężenie** - zmiana w klasie bazowej propaguje się do wszystkich potomnych. Głębokie hierarchie (więcej niż 2 poziomy) stają się nieczytelne. Kompozycja (składanie obiektów) daje elastyczność: zachowania można wymieniać w runtime, łatwiej testować w izolacji.

```python
# ŹLE - głęboka hierarchia, łamanie kontraktu
class Animal:
    def move(self): ...
class Bird(Animal):
    def move(self): return "latam"
class Penguin(Bird):
    def move(self): return "chodzę"

# DOBRZE - kompozycja przez strategię
class Animal:
    def __init__(self, name, movement):
        self.name = name
        self.move = movement

def fly():  return "latam"
def walk(): return "chodzę"

eagle   = Animal("Orzeł",   fly)
penguin = Animal("Pingwin", walk)
```

> **Wyjątek udokumentowany (LAG-Bench, warstwa `src/tasks/`, 2026-07-14):** baza `JsonOpTask` jest
> celowo bogata (predykaty jidoka/andon/poka-yoke jako metody z defaultami), NIE złożona przez
> kompozycję – po to, by uwidocznić, jak każde zadanie instancjonuje prymitywy Lean. Ryzyko
> ograniczone: hierarchia DOKŁADNIE 2 poziomy (`Task` → `JsonOpTask` → konkretne), każda metoda bazy
> ma default, a czyste polityki skalarne zostają wolnymi funkcjami (`_policies`). Uzasadnienie i
> granice: docstring `JsonOpTask` + `lag-bench/CLAUDE.md`. Poza tą warstwą #15 obowiązuje normalnie.

### 16. Prawo Demeter - rozmawiaj tylko z sąsiadami (Law of Demeter)

Zabrania "sięgania w głąb" obiektów przez łańcuchy `a.b.c.d`. Rozwiązanie: **delegowanie** - obiekt udostępnia metodę zwracającą potrzebną informację.

```python
# ŹLE - łańcuch wywołań
city = order.customer.address.city

# DOBRZE - delegowanie
class Order:
    def get_shipping_city(self):
        return self.customer.get_city()

class Customer:
    def get_city(self):
        return self.address.city
```

### 17. Struktura kodu - zasada gazety

Plik źródłowy czytamy jak artykuł: na górze **nagłówek** (nazwa klasy), potem **lead** (publiczne API), a niżej **szczegóły implementacji**. Nowy programista czyta nagłówek i lead, żeby zrozumieć *co* klasa robi - w szczegóły zagląda dopiero gdy chce wiedzieć *jak*.

```python
class InvoiceService:
    """Publiczne API na górze."""

    def create_invoice(self, order): ...
    def send_invoice(self, invoice): ...

    # --- szczegóły implementacji ---
    def _calculate_tax(self, amount): ...
    def _format_line_items(self, items): ...
    def _generate_pdf(self, invoice): ...
```

### 18. Formatowanie i spójność

Powiązane koncepcje trzymaj blisko siebie, niepowiązane rozdzielaj pustą linią. Spójne formatowanie obniża wysiłek poznawczy. Ustal konwencje w zespole na początku projektu (np. `black`, `ruff`) i **bezwzględnie ich przestrzegaj** - spójność jest ważniejsza niż indywidualne preferencje.

```python
class ReportGenerator:

    def generate(self, data):
        rows = self._prepare_rows(data)
        return self._format_output(rows)

    def _prepare_rows(self, data):
        return [self._transform(item) for item in data]

    def _format_output(self, rows):
        return "\n".join(rows)
```

---

## Grupa 5 - Zasady ogólne

> Uniwersalne reguły niezależne od paradygmatu i języka.

### 19. DRY - Nie powtarzaj się (Don't Repeat Yourself)

Każdy fragment logiki powinien istnieć **w jednym i tylko jednym miejscu**. Gdy ta sama formuła pojawia się w kilku miejscach - każda zmiana wymaga aktualizacji wszystkich kopii. Duplikacja to nie tylko skopiowane linie - to też zduplikowana *intencja*.

```python
# ŹLE - formuła zduplikowana
def get_annual_salary(e):
    return e.monthly_rate * 12 * (1 + e.bonus_pct)

def get_annual_cost(e):
    salary = e.monthly_rate * 12 * (1 + e.bonus_pct)  # kopia!
    return salary * 1.23

# DOBRZE - jedno źródło prawdy
def get_annual_salary(e):
    return e.monthly_rate * 12 * (1 + e.bonus_pct)

def get_annual_cost(e):
    return get_annual_salary(e) * 1.23
```

### 20. KISS - Prostota przede wszystkim (Keep It Simple, Stupid)

Wybieraj najprostsze rozwiązanie, które spełnia aktualne wymagania. Każda abstrakcja to koszt - koszt zrozumienia, utrzymania, wdrożenia nowego człowieka. Overengineering to jeden z najczęstszych grzechów juniorów, którzy świeżo poznali wzorce projektowe.

```python
# ŹLE - fabryka abstrakcji do odwrócenia stringa
class StringReverserFactory:
    def create_reverser(self):
        return lambda s: s[::-1]

result = StringReverserFactory().create_reverser()("hello")

# DOBRZE - prosta funkcja, zero ceremonii
def reverse_string(text):
    return text[::-1]
```

### 21. YAGNI - Nie będziesz tego potrzebować (You Ain't Gonna Need It)

Nie implementuj funkcjonalności "na zapas". Kod pisany pod wymagania, które *może* pojawią się za pół roku, trzeba utrzymywać, testować i czytać - ale nikt z niego nie korzysta. YAGNI uzupełnia KISS: rób prosto i rób **tylko to, co teraz potrzebne**.

```python
# ŹLE - pola "na wszelki wypadek"
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        self.fax = None           # kto w 2026 wysyła fax?
        self.pager_number = None
        self.matrix_handle = None

# DOBRZE - tylko to, czego wymaga sprint
class User:
    def __init__(self, name, email):
        self.name = name
        self.email = email
```

### 22. Preferuj niemutowalność (Favor Immutability)

Obiekt niemutowalny to taki, którego stanu nie da się zmienić po utworzeniu. Eliminuje bugów z niechcianymi modyfikacjami, jest bezpieczny w środowiskach wielowątkowych, łatwiej go testować. W Pythonie: `@dataclass(frozen=True)`, `NamedTuple`, `tuple`. Mutuj tylko gdy masz wyraźny powód.

```python
# ŹLE - zmienia oryginalną listę
def apply_discount(prices, pct):
    for i in range(len(prices)):
        prices[i] *= (1 - pct)
    return prices

# DOBRZE - nowa kolekcja + frozen dataclass
def apply_discount(prices, pct):
    return [price * (1 - pct) for price in prices]

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str = "PLN"

    def discounted(self, pct):
        return Money(self.amount * (1 - pct), self.currency)
```

### 23. Zasada skauta (Boy Scout Rule)

*"Zostaw kod czystszym niż go zastałeś."* Przy okazji każdego commita popraw jedną drobną rzecz: zmień skrótową nazwę, wydziel funkcję, usuń martwy kod, dodaj type hint.

```python
# Zastałeś w repozytorium:
def calc(d):
    return d * 0.23  # podatek

# Po twojej zmianie (przy okazji innego zadania):
TAX_RATE = 0.23

def calculate_tax(net_amount: float) -> float:
    return net_amount * TAX_RATE
```

---

## Grupa 6 - Jakość kodu i narzędzia

> Zasady to jedno. Narzędzia, które je egzekwują automatycznie - to drugie. Używaj obu.

### 24. Testy - TDD i zasada F.I.R.S.T.

Testy jednostkowe to siatka bezpieczeństwa, która pozwala na odważny refaktoring. TDD (Test-Driven Development): najpierw test, potem minimalny kod, potem refaktoring. Dobre testy spełniają zasadę **F.I.R.S.T.**:

- **F - Fast (szybkie):** ułamek sekundy, bo inaczej nikt nie będzie ich uruchamiać.
- **I - Independent (niezależne):** kolejność uruchomienia nie ma znaczenia.
- **R - Repeatable (powtarzalne):** ten sam wynik lokalnie i na CI.
- **S - Self-validating (samoweryfikujące):** pass lub fail, bez ręcznej interpretacji.
- **T - Timely (terminowe):** pisze się je przed lub równocześnie z kodem produkcyjnym.

```python
def test_full_time_employee_with_sufficient_tenure_is_eligible():
    employee = Employee(is_full_time=True, months_employed=12,
                        vacation_days_left=5)
    assert is_eligible_for_vacation(employee) is True

def test_new_employee_is_not_eligible():
    employee = Employee(is_full_time=True, months_employed=2,
                        vacation_days_left=5)
    assert is_eligible_for_vacation(employee) is False
```

### 25. Obsługa błędów - wyjątki zamiast kodów zwrotnych

Kody zwrotne (`return -1`, `return None`) mieszają logikę biznesową z obsługą błędów. Wyjątki oddzielają "normalny przepływ" od sytuacji wyjątkowych. Bloki `try/except` powinny być krótkie. Zasada: funkcja albo wykonuje zadanie, albo rzuca wyjątek.

```python
# ŹLE - kody zwrotne
def delete_file(path):
    if not os.path.exists(path):
        return -1
    os.remove(path)
    return 0

# DOBRZE - wyjątek wymusza obsługę
def delete_file(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        raise FileOperationError(f"Nie znaleziono: {path}")
```

### 26. Linter, formatter i PEP 8

**PEP 8** to oficjalny przewodnik stylu Pythona - definiuje konwencje nazewnictwa (`snake_case` dla funkcji, `PascalCase` dla klas), wcięcia (4 spacje), maksymalną długość linii. **Formatter** (np. `black`, `ruff format`) automatycznie poprawia styl. **Linter** (np. `ruff`, `flake8`, `pylint`) wykrywa potencjalne błędy. Konfiguruj oba w `pyproject.toml` i uruchamiaj w CI.

```toml
# pyproject.toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "SIM"]

[tool.black]
line-length = 88
```

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff          # linter
      - id: ruff-format   # formatter
```

### 27. Type hints i statyczna analiza typów

Type hints (PEP 484) to adnotacje typów w Pythonie: nie wpływają na runtime, ale pozwalają narzędziom (`mypy`, `pyright`) wykrywać błędy typów **przed uruchomieniem programu**. Dla IDE to game changer - autouzupełnianie, refaktoring i nawigacja działają dużo lepiej z typami.

```python
# ŹLE - bez typów, trzeba zgadywać
def calculate_discount(price, discount):
    return price * (1 - discount)
# price to int? float? Decimal? discount to 0.1 czy 10?

# DOBRZE - typy jako dokumentacja i walidacja
from decimal import Decimal

def calculate_discount(
    price: Decimal,
    discount_pct: Decimal,  # np. Decimal("0.15") = 15%
) -> Decimal:
    return price * (Decimal("1") - discount_pct)
```

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
disallow_untyped_defs = true
```

### 28. Code review

Code review to systematyczny przegląd kodu przez innego programistę przed mergem do głównej gałęzi. To nie "szukanie błędów" - to **transfer wiedzy**, **egzekwowanie standardów** i **ochrona przed regresją**. Najważniejsze zasady: review powinno być krótkie (max 400 linii naraz), skupione na logice (nie na formatowaniu - od tego jest linter), i konstruktywne (komentarze opisują *dlaczego*, nie tylko *co* zmienić).

```python
# Zamiast: "Źle, zmień to."
# Pisz:     "Ta metoda ma dwie odpowiedzialności
#            (walidacja + zapis). Rozważ wydzielenie
#            validate_order() - łatwiej będzie ją
#            przetestować osobno. (SRP, zasada #10)"
```

> **Praktyczny workflow:** branch -> CI (testy + ruff + mypy) -> code review -> merge. Automatyzuj co się da, żeby review skupiało się na logice i architekturze.

---

## Słowniczek trudnych terminów

| Termin                          | Definicja                                                                                                                     |
| ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| **Abstrakcja**                  | Uproszczony model, który ukrywa szczegóły implementacji i wystawia tylko to, co potrzebne do użycia.                          |
| **CI (Continuous Integration)** | Automatyczne uruchamianie testów, lintera i innych sprawdzeń przy każdym pushu do repozytorium.                               |
| **Code review**                 | Przegląd kodu przez innego programistę przed scaleniem zmian.                                                                 |
| **Delegowanie**                 | Przekazanie odpowiedzialności za zadanie innemu obiektowi, zamiast wykonywania go samodzielnie.                               |
| **Guard clause**                | Warunek na początku funkcji, który natychmiast przerywa wykonanie jeśli dane wejściowe są nieprawidłowe.                      |
| **Happy path**                  | Główny scenariusz wykonania funkcji, w którym wszystko działa poprawnie.                                                      |
| **Idempotentność**              | Wielokrotne wykonanie operacji daje ten sam wynik co jednokrotne i nie zmienia stanu systemu.                                 |
| **Interfejs**                   | Zestaw metod, które klasa zobowiązuje się udostępnić. W Pythonie: ABC lub Protocol.                                           |
| **Kontrakt (klasy)**            | Zestaw gwarancji, które klasa daje swoim użytkownikom - jakie metody udostępnia i jak się zachowują.                          |
| **Merge**                       | Scalenie zmian z gałęzi roboczej do gałęzi głównej w Git.                                                                     |
| **Mock (atrapa)**               | Fałszywy obiekt udający prawdziwy na potrzeby testów.                                                                         |
| **Mutowalny / niemutowalny**    | Mutowalny = można zmienić po utworzeniu (list, dict). Niemutowalny = nie da się zmienić (tuple, frozenset, frozen dataclass). |
| **Overengineering**             | Nadmierne komplikowanie rozwiązania ponad rzeczywiste potrzeby.                                                               |
| **Polimorfizm**                 | Zdolność różnych obiektów do reagowania na to samo wywołanie metody, każdy na swój sposób.                                    |
| **Pre-commit hook**             | Skrypt uruchamiany automatycznie przed każdym `git commit`.                                                                   |
| **Refaktoring**                 | Zmiana wewnętrznej struktury kodu bez zmiany jego zewnętrznego zachowania.                                                    |
| **Regresja**                    | Bug polegający na tym, że coś co wcześniej działało, przestało działać po zmianach.                                           |
| **Runtime**                     | Czas wykonywania programu (w przeciwieństwie do czasu kompilacji/pisania kodu).                                               |
| **Side effect**                 | Każde działanie funkcji wykraczające poza to, co sugeruje jej nazwa i wartość zwracana.                                       |
| **Sprzężenie (coupling)**       | Stopień zależności między modułami. Silne = zmiana jednego wymusza zmiany w wielu innych.                                     |
| **TDD**                         | Test-Driven Development: (1) napisz test, (2) napisz minimalny kod, (3) zrefaktoruj. Powtarzaj.                               |
| **Wielowątkowość**              | Jednoczesne wykonywanie kilku fragmentów kodu w ramach jednego programu.                                                      |
| **Workaround**                  | Tymczasowe obejście problemu - rozwiązanie które działa, ale nie jest idealne.                                                |

---

> *"Każdy głupiec potrafi napisać kod zrozumiały dla komputera. Dobry programista pisze kod zrozumiały dla ludzi."*
> — Robert C. Martin

> *"Simple is better than complex. Explicit is better than implicit. Readability counts."*
> — The Zen of Python