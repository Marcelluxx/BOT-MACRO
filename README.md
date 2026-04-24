# Desktop Automation Bot 🤖

Un bot di automazione modulare in Python progettato per giochi mobile in esecuzione su emulatori Android (come BlueStacks, LDPlayer) su Windows.

## 🌟 Funzionalità Principali

*   **Window Management Avanzato:** Trova dinamicamente la finestra dell'emulatore. Se sposti la finestra durante l'esecuzione o tra la registrazione e la riproduzione, il bot adatta automaticamente le coordinate.
*   **Registrazione Macro Relativa:** Registra i click del mouse convertendoli in coordinate relative rispetto alla finestra dell'emulatore.
*   **Riproduzione Anti-Ban:**
    *   **Easing Movimenti:** I movimenti del mouse non sono teletrasporti istantanei, ma seguono curve di accelerazione/decelerazione naturali (`pyautogui.easeOutQuad`).
    *   **Offset Casuali:** I click avvengono in un raggio di +/- 3 pixel rispetto al punto originale per simulare l'imprecisione umana.
    *   **Latenze Dinamiche:** I tempi di attesa tra un'azione e l'altra includono una piccola latenza casuale extra.
*   **Computer Vision (OpenCV):** Modulo predisposto per il template matching (es. per chiudere banner o rilevare stati del gioco in tempo reale).
*   **Fail-Safe Globali:** Hotkey di blocco emergenza (`ESC`) e sistema di fail-safe nativo spostando il mouse in uno degli angoli dello schermo.

## 🛠️ Architettura

Il progetto segue rigidi standard di modularità (PEP 8, Type Hinting, Docstrings):

*   `main.py`: Entry point. Inizializza i moduli, gestisce gli hotkeys globali (tramite la libreria `keyboard`) e avvia il Game Loop in un thread separato.
*   `window_manager.py`: Interfaccia con le API di Windows (`win32gui`) per trovare la finestra tramite titolo, estrarne il bounding box e portarla in primo piano.
*   `recorder.py`: Ascolta i click globali del mouse (`pynput.mouse`), calcola le posizioni relative basandosi sui dati di `window_manager` e salva su `macro.json`.
*   `player.py`: Legge il file JSON ed esegue i click ricalcolando le coordinate assolute in base alla posizione attuale della finestra. Include micro-attese per consentire l'interruzione immediata.
*   `vision.py`: Cattura lo schermo in modo ultrarapido tramite `mss` ed elabora i match con OpenCV (`cv2.matchTemplate`).
*   `utils.py`: Funzioni di supporto matematico e logico per l'anti-ban (movimenti pseudo-umani, calcolo degli offset).

## 🚀 Setup e Installazione

1.  **Creare un Virtual Environment:**
    ```bash
    python -m venv .venv
    ```
2.  **Attivare l'ambiente virtuale:**
    *   Su Windows:
        ```bash
        .venv\Scripts\activate
        ```
3.  **Installare le dipendenze:**
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configurazione Iniziale

Prima di lanciare il bot, è **fondamentale** indicare il titolo esatto della finestra del tuo emulatore.
1.  Apri il tuo emulatore.
2.  Annota il nome che appare in alto a sinistra sulla barra del titolo della finestra di Windows (es. `"BlueStacks App Player"` o `"LDPlayer"`).
3.  Apri `main.py` e modifica la costante `WINDOW_TITLE`:
    ```python
    WINDOW_TITLE = "Nome Esatto Della Finestra"
    ```

## 🎮 Come Utilizzare il Bot

Avvia il bot da terminale:
```bash
python main.py
```

### Hotkeys Globali

Una volta avviato, il bot ascolterà in background queste scorciatoie da tastiera, indipendentemente da quale finestra sia attiva:

*   `F8` - **Inizia / Ferma Registrazione:** 
    1.  Premi F8. Il bot inizierà a registrare i tuoi click.
    2.  Clicca i punti dell'emulatore. Tutti i click fuori dalla finestra verranno ignorati.
    3.  Premi di nuovo F8 per fermare. I dati verranno salvati nel file `macro.json`.
*   `F9` - **Avvia / Ferma Riproduzione:** 
    Avvia un loop infinito. Il bot eseguirà i movimenti del mouse con animazioni fluide, offset causali e calcoli relativi alla posizione in tempo reale della finestra. Premi di nuovo F9 per tornare allo stato di riposo (IDLE).
*   `ESC` - **Arresto di Emergenza:** Termina brutalmente e immediatamente l'esecuzione del programma.

*(Alternativa Fail-Safe: Se muovi fisicamente e rapidamente il tuo mouse in uno dei 4 angoli estremi del tuo monitor, il bot si fermerà lanciando un'eccezione di fail-safe).*
