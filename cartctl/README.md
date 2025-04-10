# 1. projektu ATA LS 2024/25 - Dokumentace testů

### Autor: Bc. Adam Hos \<xhosad00>

## Nejasnosti/chyby ve specifikaci

Rozporu ve Specifikace chování:

> Požadavek "F-06 In unloading-only mode, the cart shall not perform any other loading or unloading except for priority cargo." Je v rozporu s "V tomto režimu (prioritní) vozík ignoruje jiné požadavky na převoz a zamíří přímo k cílové zastávce prioritního materiálu"

Dále je požadována jako korektní varinata chování, že vozík v režimu UNLOAD_ONLY bude skutečně poze vykládat a jiný prioritní materiál nenaloží (tak jak je to v aktuální implementaci).
Pokud by byla tato doměnka špatná, tak by vzrostla sekce UNLOAD_ONLY Mode o nakládání prioritního materiálu a vykládání více než jednoho materiálu.

## Testovací cesty

| Id | cesta/uzly   | pokryté požadavky |
| :------------------ | :----------- | :---------------- |
| 1| Cargo.dot: Created->Loaded | F-02|
| 2| Cargo.dot: Created->Loaded->SetPriority |F-03|
| 3|Cargo.dot: Created->Loaded-(Picked up)>SetPriority |F-04  |
| 4|Cargo.dot: Created->Loaded-(After 60s, force pickup)>SetPriority |F-04  |
| 5|CartStatus: Loading->UNLOAD_ONLY (UO) |F-05 |
| 6|CartCtl: UNLOAD_ONLY->UNLOAD_ONLY |F-06 |
| 7|CartCtl: UNLOAD_ONLY->NORMAL |F-07 |
| 8|CartStatus: Moving->Moving |F-08|
| 9|CartStatus: Loading->Loading->Loading |F-09|
|10|CartStatus: Unloading->Unloading->Unloading |F-09|
|11|CartStatus: Loading->Loading->Moving->Unloading->Unloading |F-09|
|12|Cargo.dot: Created->Terminated |F-10|
|13|CartStatus: IDLE->NORMAL |P-01|

Je několik požadavků, které v cestách nejsou zahrnuty z následujících důvodů:
F-01 - Neexistuje žádný modul, který by automaticky generoval nové požadavky
F-08 - 


## Vstupní parametry testů

| Id | stručný popis |
| :---------------------- | :------------ |
| cartWeight | Maximální váha vozíku|
| slots| Počet slotů vozíku |
| cargoReq| Seznam n-tic reprezentující požadavek vytvořen ve formátu: [(src, dst, weight, name), ...]|
| reqTime|Seznam časů, kdy byli vytvořené požadavky |


## Tabulka testů


| Id |cartWeight|slots|cargoReq|reqTime| očekávaný výsledek | pokryté testovací cesty |  název testovací metody |
| :--- | :------ | :------- | :---- |:---- |:---- |:---- |:---- |
| 1|150 |4 |[('A','B',30,'broccoli'), ('B','C',100,'carrot'), ('C','A',10,'daikon'), ('C','D',20,'onion')]| [1, 2, 70, 90] | Kontrolér příjmá požadavky v daných časech, postupně je úspěšně plní (nakládá a vykládá ve správných stanicích) a žádný materiál se nestane prioritním | | test_happy_no_prio|
| 2|150 |4 |[('B','D',150,'broccoli'), ('D','B',30,'carrot'), ('A','B', 40,'daikon')]| [1, 2, 70] |Kontrolér příjmá požadavky v daných časech, postupně je úspěšně plní. Materiál `carrot` se stane prioritní. Po cestě na stanici vykládání `carrot` se nenaloží `daikon` kvůli UNLOAD_ONLY, i když má vozík volný slot a kapacitu a `daikon` je na cestě | | test_happy_prio|
|3|[50, 150, 500]|[0, 1, 2, 3, 4, 5]|-|-|Postupně zkouší kombinace vozíku. Když je zvolená špatná kombinace, očekává CartError|-|test_cart_props_slots|
|4|2|[0, 1, 50, 99.9, 150, 200, 500, 501]|-|-|Postupně zkouší kombinace vozíku. Když je zvolená špatná kombinace, očekává CartError|-|test_cart_props_weight|
|5|150|4|[('A','D',50,'broccoli'), ('A','D',1000,'bigBroccoli'), ('A','D',-1,'bigBroccoli')]|0|Vytvoří několik požadavků. U přidávání několika nevalidních požadavků očekává CartError||test_cart_props_bad_req|



## Diagramy

Jednotlivé stavové diagramy

> ### Stavový diagram nákladu
> 
> ![alt text](./diagrams/Cargo.png "Cargo")
>
> Diagram popisuje stavy meteriálu od prvotní žádosti až po vyložení nebo zahození požadavku. Požadavku je nastavena priorita po šedesáti sekundách. 
> 
> Problémový je ale případ, kdy přetrvá od nastavení dalších 60s. Ze specifikace chování: "Pokud takový materiál (prioritní) stále není naložen do další 1 minuty a vozík má volnou kapacitu, materiál se okamžitě naloží a vozík přepne do režimu pouze-vykládka."Pomiňuje ale fakt, že pokud vozík není v danné stanici, materiál se nemůže naložit

> ### Stavový diagram CartCtl
> 
> ![alt text](./diagrams/CartCtl.png "CartCtl")
>
> Diagram popisuje stavy CartCtl. Diagram je využit v několika testovacích cestách. Také slouží jako zjednodušený přehled stavů vozíku.

> ### Stavový diagram Vozíku
>
> Seskupuje dohromady Cart a CartCtl. Figuruje jako hlavní stavový diagraf pro tvoření testů.
> Jako počáteční stav má IDLE, ve kterém je pokud nemá žádný aktivní požadavek nebo nevyložený náklad. Přechod do NORMAL proběhne když je registrován požadavek. Zbytek grafu slouží pro plnění požadavků.
> * Loading - při provedení hrany `Loading` se naloží jeden materiál z aktuální stanice. Pokud je matirál prioritní, přepíná se do UNLOAD_ONLY režimu
> * Moving - První přesun do Moving sám o sobě nedělá přesun vozíku. Figuruje tedy taky jako spoj mezi stavy Loading a Unloading, i když se vozík nepřesune do jiné stanice. Až provedením hrany `Move to dst` se přesune do další dosažitelné stanice, která byla zvolena plánovacím algoritmem.
> * Unloading - při provedení hrany `Unloading` se vyloží jeden materiál z aktuální stanice.
> 
> Stavy Moving a Unloading v podgrafu UNLOAD ONLY Mode figurují stejně jako v normálním provozu, až na to, že při vyložení prioritního materiálu se hranou `All prio cargo unloaded` přesune do stavu NORMAL.
> ![alt text](./diagrams/CartStatus.png "CartStatus")
