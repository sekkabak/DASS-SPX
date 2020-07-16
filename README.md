# DASS-SPX

Opis oraz prosta implementacja protokołu DASS-SPX

## Geneza protokołu
DASS - Distributed Authentication Security Service – usługa uwierzytelniania klient - klient oparta na kluczu publicznym. 
Jej prototyp został użyty w protokole SPX, którego budowa i cele zbliżone są do protokołu Kerberos. Obsługuje on uwierzytelnianie użytkowników i podmiotów sieciowych, dystrybucję kluczy, ochronę danych w tranzycie danych, pojedyncze logowania, przekazywanie uprawnień na podstawie tożsamości, skalowalność do bardzo dużego środowiska.
Pierwsze publikacje DASS/SPX pojawiły się na początku lat 90. XX w. DASS opisuje architekturę, natomiast Sphinx(SPX) odnosi się do implementacji protokołu.

## Opis protokołu

1. Alice i Bob generują klucze prywatne oraz publiczne i wysyłają publiczne do trzeciej zaufanej strony.
2. Trzecia zaufana strona podpisuje otrzymane kopie kluczy publicznych. Podpis składa się z wykonania na wiadomości funkcji skrótu SHA-256, a następnie zaszyfrowania skrótu algorytmem RSA.
3. Alice wysyła do trzeciej zaufanej strony wiadomość zawierającą nazwę Boba.
4. Trzecia zaufana strona przesyła do Alice klucz publiczny Boba podpisany kluczem prywatnym trzeciej zaufanej strony.
5. Alice dokonuje weryfikacji podpisu trzeciej zaufanej strony, sprawdzając, czy klucz, który otrzymała jest aktualnym kluczem publicznym Boba. Dalej generuje losowy klucz tajny i losowe klucz publiczny oraz klucz prywatny, szyfruje czas, używając do tego klucza tajnego, dokonuje podpisu okresu ważności klucza, swojego identyfikatora oraz losowego klucza przy użyciu swojego klucza prywatnego, dokonuje szyfrowania klucza tajnego za pomocą klucza publicznego Boba i podpisuje przy pomocy swojego losowego klucza prywatnego. Całość wysyła do Boba. Szyfrowanie asymetryczne odbywa się przy użyciu algorytmu RSA, do symetrycznego natomiast używany jest AES.
6. Bob przesyła do trzeciej zaufanej strony wiadomość zawierającą nazwę Alice.
7. Trzecia zaufana strona wysyła do Boba klucz publiczny Alice, który podpisała za pomocą swojego klucza prywatnego.
8. Bob sprawdza podpis trzeciej zaufanej strony, by wiedzieć, że otrzymał aktualny klucz publiczny Alice, dokonuje sprawdzenia podpisu Alice i odtwarza jej losowy klucz prywatny, dokonuje sprawdzenia podpisu i odtwarza losowy klucz tajny Alice za pomocą swojego klucza prywatnego.

# Uruchamianie
Wszystkie biblioteki wymagane do uruchomienia projektu są wylistowane w requirements.txt. Można je zainstalować za pomocą komendy `pip install -r requirements.txt`.

Do przetestowania działania protokołu należy uruchomić 3 skryptu pythona\
`python Server.py`\
`python Klient.py`\
`python Klient2.py`

# Przykład działania
![Uruchomienie](https://github.com/sekkabak/DASS-SPX/blob/master/Przechwytywanie.PNG "Logo Title Text 1")

# Przydatne komendy
pyuic5 -x Klient.ui -o KlientUI.py
