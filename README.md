# BOT-MACRO — Visual Automation Bot 🤖

**BOT-MACRO** è un software di automazione professionale progettato per emulatori Android (LDPlayer, BlueStacks) e applicazioni Windows. A differenza dei semplici registratori di macro, offre un **Editor Visuale Drag & Drop** e un sistema di **Visione Artificiale** intelligente per gestire popup e imprevisti.

---

## 🌟 Funzionalità Principali

*   **🎨 Editor Visuale:** Costruisci le tue macro trascinando blocchi-azione (Click, Delay, Vision Scan, Sub-Macro).
*   **🖱️ Registrazione Intelligente:** Registra i tuoi click in tempo reale. Usa **F7** durante la registrazione per inserire "Checkpoints" di visione.
*   **👁️ Multi-Asset Vision:** Il bot "vede" lo schermo. Riconosce automaticamente tutti i pulsanti/immagini nella cartella `assets/` e li clicca per chiudere popup o confermare azioni.
*   **♻️ Gestione Popup a Strati:** Se ci sono più popup sovrapposti, il bot li chiude uno alla volta rinfrescando lo screenshot dopo ogni click.
*   **🛡️ Sistema Anti-Ban:**
    *   **Movimenti Umani:** Il mouse si muove con curve di accelerazione naturali.
    *   **Randomizzazione:** Ogni click ha un piccolo offset casuale (+/- 3px) e ritardi variabili per simulare un utente umano.
*   **🧩 Modularità:** Puoi creare piccole macro e inserirle dentro macro più grandi come "sotto-azioni".

---

## 🚀 Installazione Rapida

1.  **Requisiti:** Assicurati di avere [Python 3.10+](https://www.python.org/downloads/) installato.
2.  **Clona o scarica** questo progetto sul tuo PC.
3.  **Crea un ambiente virtuale (consigliato):**
    ```bash
    python -m venv .venv
    .venv\Scripts\activate
    ```
4.  **Installa le dipendenze:**
    ```bash
    pip install -r requirements.txt
    ```

---

## 🎮 Guida all'Uso (GUI)

Lancia l'interfaccia grafica con:
```bash
python main.py
```

### 1. Preparazione Assets
Inserisci nella cartella `assets/` i file `.png` delle immagini che vuoi che il bot riconosca (es. la "X" rossa per chiudere i popup, il tasto "OK", ecc.). Il bot scansionerà questa cartella automaticamente.

### 2. Creare una Macro
Esistono due modi per costruire la tua automazione:

*   **Metodo Manuale:** Trascina i blocchi dal pannello sinistro (**Toolbox**) al centro (**Timeline**).
*   **Metodo Registrazione:**
    1.  Clicca **⏺ Registra** (o premi **F8**).
    2.  Esegui i click sull'emulatore.
    3.  **IMPORTANTE:** Se appare un popup o vuoi che in quel punto il bot controlli se ci sono pulsanti da cliccare, premi **F7**. Verrà inserita una "Flag" di visione.
    4.  Premi di nuovo **F8** per fermare.

### 3. Editing Visuale
*   **Riordina:** Trascina i blocchi su e giù nella timeline per cambiare l'ordine.
*   **Modifica:** Clicca su un blocco per vederne le proprietà a destra (coordinate, tempi di attesa, soglia di precisione della visione).
*   **Sub-Macro:** Trascina un file salvato dalla sezione "Azioni Salvate" per eseguire una macro dentro l'altra.

### 4. Esecuzione
Premi **▶ Esegui** (o **F9**). Il bot porterà in primo piano la finestra dell'emulatore (default: "LDPlayer") e inizierà il loop.

---

## ⌨️ Scorciatoie da Tastiera (Hotkeys)

Questi tasti funzionano globalmente, anche se l'app è in background:

| Tasto | Funzione |
| :--- | :--- |
| **F7** | **Inserisci Flag Visione** (Solo durante registrazione) |
| **F8** | **Avvia / Ferma Registrazione** |
| **F9** | **Avvia / Ferma Riproduzione (Loop)** |
| **ESC** | **STOP DI EMERGENZA** (Chiude tutto istantaneamente) |

---

## ⚙️ Configurazione Avanzata

Se la tua finestra dell'emulatore ha un nome diverso da "LDPlayer":
1.  Apri `main.py`.
2.  Cambia la costante `WINDOW_TITLE` (riga 46 per CLI, riga 38 per GUI in `gui/main_window.py`).

---

## 🛠️ Risoluzione Problemi

*   **Il bot non clicca nel punto giusto:** Assicurati che l'emulatore non sia ridimensionato in modo strano. Il bot usa coordinate relative alla finestra, ma la risoluzione interna deve essere coerente.
*   **Il Vision Scan non trova i pulsanti:** Controlla che le immagini in `assets/` siano ritagliate in modo preciso e abbiano lo sfondo trasparente o coerente con il gioco. Prova ad abbassare la "Soglia" (Threshold) nelle proprietà del blocco Vision Scan (es. 0.7 invece di 0.8).
*   **Arresto di Emergenza:** Se il bot impazzisce, muovi il mouse velocemente in uno dei **quattro angoli dello schermo** per attivare il fail-safe di PyAutoGUI.
