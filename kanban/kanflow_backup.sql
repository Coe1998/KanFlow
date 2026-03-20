BEGIN TRANSACTION;
CREATE TABLE labels (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                name       TEXT    NOT NULL,
                color      TEXT    NOT NULL DEFAULT '#6C63FF'
            );
INSERT INTO "labels" VALUES(1,2,'DA DISCUTERE','#FF6584');
INSERT INTO "labels" VALUES(2,2,'DA MOSTRARE','#3A86FF');
INSERT INTO "labels" VALUES(3,3,'NEW FEATURE','#FF6584');
INSERT INTO "labels" VALUES(4,2,'DA TESTARE','#43B89C');
CREATE TABLE project_files (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                rel_path   TEXT    NOT NULL,
                note       TEXT    NOT NULL DEFAULT '',
                pinned_at  TEXT    NOT NULL, is_dir INTEGER NOT NULL DEFAULT 0,
                UNIQUE(project_id, rel_path)
            );
INSERT INTO "project_files" VALUES(3,2,'test_generator','','2026-03-20T09:56:07.535407',1);
CREATE TABLE projects (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                color      TEXT    NOT NULL DEFAULT '#6C63FF',
                created_at TEXT    NOT NULL
            , notes TEXT NOT NULL DEFAULT '', git_path TEXT NOT NULL DEFAULT '');
INSERT INTO "projects" VALUES(2,'TEST GENERATOR','#6C63FF','2026-03-19T08:51:45.793328','- per buildare il progetto bisogna lanciare questa riga:

```
pyinstaller --onefile --paths . --collect-all tree_sitter_c_sharp main.py
```

- per visual studio: ora si posso inserire 2 strumenti diversi:
1)
titolo: Analizza Classe per Test IA
comando: C:\Users\cozmin.bejinari\Desktop\dist\TestGenerator.exe
argomenti: $(ItemPath) --generate
directory iniziale: $(ItemDir)

2)
titolo: TestGenerator - Bulk Progetto    
comando: C:\Users\cozmin.bejinari\Desktop\dist\TestGenerator.exe
argomenti:  $(ProjectDir) --generate --recursive -f mstest
directory iniziale: $(ProjectDir)  

inoltre ora si puo pure definire un framework di test specifico, sia per il singolo test che per il bulk, andandolo a inserire in arguments con la sigla -f seguito dal framework scelto:
- xunit
- nunit
- mstest
se non si mette -f di default viene messo mstest.



implementato dashboard per KPI:
 Dashboard mostra:
  - KPI: ore risparmiate, file processati, scenari generati, tasso di successo
  - Risparmio aziendale: formula dettagliata X scenari × 20 min = Y ore → Z giorni lavorativi
  - Timeline 30 giorni: file e scenari per giorno
  - Distribuzione framework: mstest / xunit / nunit
  - Performance AI per modello: tempo medio in ms per ogni modello usato
  - File più complessi: top 10 classi per numero di scenari
  - Tabella sessioni recenti: con ID, timestamp, framework, esito, tempo AI

accessibile lanciando:
main.exe --dashboard
oppure
python main.py --dashboard

','C:\Users\cozmin.bejinari\source\repos\Taglio.Lab.UnitTestGenerator');
INSERT INTO "projects" VALUES(3,'KanFlow – Dev Board','#43B89C','2026-03-19T09:54:45.576329','per lanciare il progetto, mettersi sulla root dove è presente app.py e lanciare:

```
python app.py
```

successivamente collegarsi a:
http://localhost:5000/','');
INSERT INTO "projects" VALUES(4,'MyGymPlan','#FFBE0B','2026-03-20T11:12:07.984955','supabase pwd db:
frU/2SE@t$RcdDB


📋 Setup MyGymPlan su nuovo PC
1. Prerequisiti da installare

Node.js v18.17+ → nodejs.org (versione LTS)
Git → git-scm.com
VS Code → code.visualstudio.com

2. Clona il repository
bashgit clone https://github.com/Coe1998/mygymplan.git
cd mygymplan
3. Installa le dipendenze
bashnpm install
4. Crea il file .env.local
Crea il file .env.local nella root del progetto con questi valori (li trovi su Supabase e Stripe):
envNEXT_PUBLIC_SUPABASE_URL=https://xxxxxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyXXXXXXXX...
SUPABASE_SERVICE_ROLE_KEY=eyXXXXXXXX...

STRIPE_SECRET_KEY=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

NEXT_PUBLIC_APP_URL=http://localhost:3000
Dove trovare le credenziali Supabase:

Vai su supabase.com → progetto mygymplan
Project Settings → API
Copia Project URL, anon public e service_role

5. Avvia il progetto
bashnpm run dev
```
Apri **http://localhost:3000**

---

## 🗄️ Database (Supabase)
- Progetto: `mygymplan` su supabase.com
- Tutte le migration sono in `supabase/migrations/`
- Se il DB è già configurato non serve fare nulla
- Se riparto da zero: eseguire tutti i file `.sql` in `supabase/migrations/` in ordine numerico dal SQL Editor di Supabase

**Funzioni SQL custom installate:**
- `get_user_id_by_email` — cerca utente per email (usata per aggiungere clienti)

---

## 📁 Struttura cartelle principali
```
src/
├── app/
│   ├── (auth)/login e register
│   ├── (coach)/coach/ → dashboard, clienti, schede, esercizi, analytics
│   ├── (cliente)/cliente/ → dashboard, allenamento, progressi
│   └── api/coach/aggiungi-cliente/
├── components/
│   ├── coach/ → CoachSidebar
│   └── shared/ → LogoutButton
├── lib/supabase/ → client.ts, server.ts, middleware.ts
└── types/ → index.ts

🔑 Account di test

Coach: bogdancosminbejinari@gmail.com
Cliente: bogdancosminbejinari+cliente@gmail.com','');
CREATE TABLE task_labels (
                task_id  INTEGER NOT NULL REFERENCES tasks(id)  ON DELETE CASCADE,
                label_id INTEGER NOT NULL REFERENCES labels(id) ON DELETE CASCADE,
                PRIMARY KEY (task_id, label_id)
            );
INSERT INTO "task_labels" VALUES(60,3);
INSERT INTO "task_labels" VALUES(53,3);
INSERT INTO "task_labels" VALUES(5,4);
CREATE TABLE tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id  INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                title       TEXT    NOT NULL,
                description TEXT    NOT NULL DEFAULT '',
                status      TEXT    NOT NULL DEFAULT 'todo',
                position    INTEGER NOT NULL DEFAULT 0,
                created_at  TEXT    NOT NULL
            );
INSERT INTO "tasks" VALUES(4,2,'Cambiare provider AI da Gemini a OpenAI','','todo',0,'2026-03-19T09:08:17.528239');
INSERT INTO "tasks" VALUES(5,2,'Supportare l''uso del programma su più classi contemporaneamente','titolo: TestGenerator - Bulk Progetto    
comando: C:\Users\cozmin.bejinari\Desktop\dist\TestGenerator.exe
argomenti:  $(ProjectDir) --generate --recursive -f mstest
directory iniziale: $(ProjectDir)

EDIT: 
ancora da testare','in_progress',0,'2026-03-19T09:08:17.849977');
INSERT INTO "tasks" VALUES(6,2,'Implementare rilevamento automatico versioni Moq/FluentAssertion','Riconoscere le versioni installate di Moq, Fluent Assertions e altri pacchetti simili sul PC.','done',7,'2026-03-19T09:08:18.102046');
INSERT INTO "tasks" VALUES(7,2,'Utilizzare versioni rilevate per la creazione del .csproj','Inserire le versioni rilevate automaticamente di Moq, Fluent Assertions, ecc. nel file .csproj.','done',8,'2026-03-19T09:08:18.196604');
INSERT INTO "tasks" VALUES(8,2,'Implementare fallback per versioni pacchetti più recenti','Se le versioni di Moq, Fluent Assertions, ecc. non sono rilevate, utilizzare le versioni più recenti disponibili.','done',15,'2026-03-19T09:08:18.434752');
INSERT INTO "tasks" VALUES(9,2,'Estendere compatibilità a framework di test multipli','Rendere il programma utilizzabile con framework di test diversi da MSTest (es. NUnit, xUnit).','done',16,'2026-03-19T09:08:18.527728');
INSERT INTO "tasks" VALUES(10,2,'Verificare funzionamento su interfacce','Testare e assicurarsi che il programma funzioni correttamente quando interagisce con interfacce.','todo',1,'2026-03-19T09:08:18.766241');
INSERT INTO "tasks" VALUES(11,2,'Installer: Aggiungere variabile di sistema per AI KEY','Assicurarsi che l''installer crei e configuri la variabile di sistema per la chiave API dell''AI.','in_progress',2,'2026-03-19T09:08:18.860989');
INSERT INTO "tasks" VALUES(12,2,'Installer: Configurare strumenti in Visual Studio (se possibile)','Esplorare la possibilità che l''installer configuri automaticamente gli strumenti necessari in Visual Studio.','in_progress',3,'2026-03-19T09:08:19.111750');
INSERT INTO "tasks" VALUES(13,2,'Ricercare esposizione API di Codex','Verificare se l''API di Codex è pubblicamente disponibile o accessibile per l''integrazione.

EDIT: esiste un parametro chiamato temperature, dove praticamente più è basso piu il programma fa ragionamenti complessi','done',3,'2026-03-19T09:08:19.192617');
INSERT INTO "tasks" VALUES(14,2,'Analizzare pricing per Llama locale','Ricercare e confrontare i costi associati all''esecuzione di modelli Llama in locale.

EDIT:
1 - free: 0$
2 - pro: 20$ month
3 - max: 100$ month

https://ollama.com/pricing','done',4,'2026-03-19T09:08:19.460222');
INSERT INTO "tasks" VALUES(15,2,'Implementare sistema di logging','Aggiungere funzionalità di logging per tracciare eventi e debug del programma.','done',5,'2026-03-19T09:08:19.541080');
INSERT INTO "tasks" VALUES(16,3,'Setup progetto Flask','Struttura cartelle: /templates, /static/css, /static/js. Entry point app.py con factory create_app().','done',5,'2026-03-19T09:54:45.591347');
INSERT INTO "tasks" VALUES(17,3,'Database SQLite con sqlite3 built-in','database.py con get_conn(), init_db(), tabelle projects e tasks. Nessuna dipendenza esterna oltre Flask.','done',4,'2026-03-19T09:54:45.610355');
INSERT INTO "tasks" VALUES(18,3,'Modello Project','Tabella projects: id, name, color, notes, created_at. Helper CRUD: get_all_projects, create_project, update_project, delete_project.','done',6,'2026-03-19T09:54:45.630920');
INSERT INTO "tasks" VALUES(19,3,'Modello Task','Tabella tasks: id, project_id (FK cascade), title, description, status, position, created_at.','done',7,'2026-03-19T09:54:45.650922');
INSERT INTO "tasks" VALUES(20,3,'REST API – Progetti','GET /api/projects, POST /api/projects, PUT /api/projects/<id>, DELETE /api/projects/<id>, GET /api/projects/<id>.','done',8,'2026-03-19T09:54:45.668937');
INSERT INTO "tasks" VALUES(21,3,'REST API – Task','GET /api/projects/<id>/tasks, POST /api/projects/<id>/tasks, PUT /api/tasks/<id>, DELETE /api/tasks/<id>.','done',9,'2026-03-19T09:54:45.687919');
INSERT INTO "tasks" VALUES(22,3,'Pagina Home – lista progetti','Grid responsive di project card con color bar, nome, contatore task e bottoni rename/delete.','done',10,'2026-03-19T09:54:45.707934');
INSERT INTO "tasks" VALUES(23,3,'Kanban board – layout 3 colonne','Colonne TODO / IN PROGRESS / DONE con header badge colorati e contatore card per colonna.','done',11,'2026-03-19T09:54:45.725515');
INSERT INTO "tasks" VALUES(24,3,'Drag & drop tra colonne','HTML5 DnD con placeholder animato, highlight colonna target, aggiornamento status via API al drop.','done',12,'2026-03-19T09:54:45.743497');
INSERT INTO "tasks" VALUES(25,3,'Modal Crea/Modifica Task','Textarea per titolo e descrizione, status tab selector, salvataggio con Invio. Pulsante Delete in edit mode.','done',13,'2026-03-19T09:54:45.763342');
INSERT INTO "tasks" VALUES(26,3,'Modal Crea/Rinomina Progetto','Input nome + 6 colour swatches. Riutilizzato per create e rename cambiando titolo e label del bottone.','done',14,'2026-03-19T09:54:45.782327');
INSERT INTO "tasks" VALUES(27,3,'Confirm modal per delete','Modal di conferma riutilizzabile per delete progetto e delete task, con messaggio contestuale.','done',15,'2026-03-19T09:54:45.797314');
INSERT INTO "tasks" VALUES(28,3,'Toast notification','Messaggio toast bottom-right con varianti success/error, auto-dismiss dopo 2.8 s.','done',16,'2026-03-19T09:54:45.813229');
INSERT INTO "tasks" VALUES(29,3,'Design system dark mode','CSS custom properties per superfici, testi, accenti. Font Syne (display) + DM Sans (body). Scrollbar personalizzata.','done',17,'2026-03-19T09:54:45.830886');
INSERT INTO "tasks" VALUES(30,3,'Progress bar completamento progetto','Query SQL con SUM(CASE WHEN status=''done'') per calcolare %, progress bar animata con shimmer. Stato verde+glow al 100%.','done',18,'2026-03-19T09:54:45.849826');
INSERT INTO "tasks" VALUES(31,3,'Refresh progress al ritorno dalla board','refreshCardProgress() chiama GET /api/projects/<id> al DOMContentLoaded e aggiorna barra senza reload.','done',19,'2026-03-19T09:54:45.870782');
INSERT INTO "tasks" VALUES(32,3,'Integrazione Gemini AI – estrazione task','gemini.py chiama gemini-2.5-flash via urllib (no deps). Endpoint POST /api/projects/<id>/extract-tasks restituisce preview senza salvare.','done',20,'2026-03-19T09:54:45.891890');
INSERT INTO "tasks" VALUES(33,3,'UI estrazione AI – modal 2 step','Step 1: textarea appunti. Step 2: preview card selezionabili con checkbox, badge status inferito, select-all toggle.','done',21,'2026-03-19T09:54:45.912434');
INSERT INTO "tasks" VALUES(34,3,'Note di progetto – drawer laterale','Slide-in drawer con textarea monospace, toolbar formattazione, auto-save debounced 3 s, Ctrl+S.','done',22,'2026-03-19T09:54:45.933198');
INSERT INTO "tasks" VALUES(35,3,'Markdown renderer custom','Parser da zero: headings, **bold**, *italic*, `code`, fenced code blocks con label lingua e bottone copia, liste, blockquote, HR.','done',23,'2026-03-19T09:54:45.952166');
INSERT INTO "tasks" VALUES(36,3,'Migrazione DB safe per colonna notes','PRAGMA table_info + ALTER TABLE ADD COLUMN per aggiornare DB esistenti senza perdere dati.','done',24,'2026-03-19T09:54:45.970054');
INSERT INTO "tasks" VALUES(37,3,'Bug fix: .hidden scomparso dal CSS','La regola .hidden { display:none !important } era stata rimossa per errore durante una str_replace, causando la visualizzazione di tutti i modal all''avvio.','done',25,'2026-03-19T09:54:45.988071');
INSERT INTO "tasks" VALUES(38,3,'Seed progetto KanFlow nel proprio board','Script seed_kanflow_project.py che inserisce il dev board di KanFlow come primo progetto reale nell''app.','done',26,'2026-03-19T09:54:46.013315');
INSERT INTO "tasks" VALUES(39,3,'Responsive mobile completo','Il drawer note e la board vanno ottimizzati per viewport < 480px. Testare drag & drop su touch.','todo',0,'2026-03-19T09:54:46.033096');
INSERT INTO "tasks" VALUES(40,3,'Ordinamento manuale task nella stessa colonna','Drag & drop all''interno della stessa colonna con aggiornamento del campo position via API.','done',3,'2026-03-19T09:54:46.053582');
INSERT INTO "tasks" VALUES(41,3,'Filtro / ricerca task','Barra di ricerca nella board per filtrare card per testo. Highlight del termine cercato nelle card.','todo',1,'2026-03-19T09:54:46.077024');
INSERT INTO "tasks" VALUES(42,3,'Etichette colorate per i task','Tag personalizzabili per categoria (es. bug, feature, docs). Visibili come pillole sulle card.','done',2,'2026-03-19T09:54:46.097133');
INSERT INTO "tasks" VALUES(43,3,'Data di scadenza per i task','Campo due_date opzionale. Badge rosso sulla card se scaduto, giallo se in scadenza entro 2 giorni.','todo',3,'2026-03-19T09:54:46.118145');
INSERT INTO "tasks" VALUES(44,3,'Export board in Markdown / JSON','Bottone nella board per scaricare tutti i task come file .md strutturato o .json per backup.','todo',4,'2026-03-19T09:54:46.139256');
INSERT INTO "tasks" VALUES(45,2,'suddivisione del progetto in classi','','done',9,'2026-03-19T10:05:48.182863');
INSERT INTO "tasks" VALUES(46,2,'generazione automatica di script da inserire in ia','passaggio iniziale nel quale ancora l''utente doveva manualmente copiare il codice che poi l''ia generava e creare il test da li','done',10,'2026-03-19T10:08:10.580450');
INSERT INTO "tasks" VALUES(47,2,'utilizzo di tree sitter per analizzare tutte le parti del codice','','done',11,'2026-03-19T10:09:19.255689');
INSERT INTO "tasks" VALUES(48,2,'escludere l''utilizzo di code coverage','grazie a treesitter riusciamo a evitare l''utilizzo di code coverage, il quale gia inizialmente non comprendeva il 100% dei casi ma solamente il 100% del codice utilizzato, e di conseguenza risparmiare tempo','done',12,'2026-03-19T10:12:18.018654');
INSERT INTO "tasks" VALUES(49,2,'analisi su tempo salvato','analizzare quanto tempo si risparmia ogni singolo user ogni volta che utilizza test generator, grazie a strumenti come cristalreport o altro

EDIT: usato flask internamente al programma, inoltre aggiunta possibilità di integrare in futuro e centralizzare su un unico server tutte le sessioni di generazione automatica di test in modo da avere piu dati possibili e quindi essere in grado di fare ragionamenti su quale possa essere l''ia migliore da usare la piu precisa o la piu veloce','done',6,'2026-03-19T10:13:29.766147');
INSERT INTO "tasks" VALUES(50,2,'semplificare il main','','done',13,'2026-03-19T10:13:42.000569');
INSERT INTO "tasks" VALUES(51,2,'risoluzione del caricamento del test modificando il .sln','','done',14,'2026-03-19T10:14:45.465656');
INSERT INTO "tasks" VALUES(52,3,'integrazione con git x documentazione','dare la possibilità in automatico di poter collegare un progetto a un ramo su git in modo da avere un qualcosa che punta direttamente ai file per creare documentazione automatica','done',1,'2026-03-19T10:19:07.842083');
INSERT INTO "tasks" VALUES(53,3,'integrazione con git per gestione task','da capire se esiste un modo per collegare git e l''esistenza dei task','todo',5,'2026-03-19T10:20:12.071066');
INSERT INTO "tasks" VALUES(54,3,'possibilità di renderlo un sistema di ticketing','','todo',6,'2026-03-19T10:20:43.014393');
INSERT INTO "tasks" VALUES(55,3,'possibilità di gestire una pianificazione','','todo',7,'2026-03-19T10:21:50.692931');
INSERT INTO "tasks" VALUES(56,3,'aggiungere il login e la registrazione','','todo',8,'2026-03-19T10:41:50.599004');
INSERT INTO "tasks" VALUES(57,3,'avere la possibilità di condividere i project con più utenti','','todo',9,'2026-03-19T10:42:27.330482');
INSERT INTO "tasks" VALUES(58,3,'possibilità di fare reverse engeneering sui progetti','partire da un progetto fisico per crare un progetto su KanFlow con tutti i relativi task','todo',10,'2026-03-19T11:01:25.398067');
INSERT INTO "tasks" VALUES(59,3,'Filtro / Ricerca progetti','','todo',2,'2026-03-19T11:08:34.540235');
INSERT INTO "tasks" VALUES(60,3,'On click del task aprire il task in preview','','done',0,'2026-03-19T15:24:50.494353');
INSERT INTO "tasks" VALUES(61,2,'fare prompt in inglese','cambiare la lingia o almeno l''output dei prompt che mandiamo a gemini o openai o claude','in_progress',1,'2026-03-20T08:10:24.715333');
INSERT INTO "tasks" VALUES(62,2,'pricing codex','API (pay-as-you-go, per sviluppatori)

Se usi Codex via API (CLI, IDE, backend), paghi a consumo per token:

Esempi (2026):

GPT-5 Codex

Input: ~$1.25 / 1M token

Output: ~$10 / 1M token

Codex Mini (più economico) pero meno "intelligente"

Input: ~$0.75 / 1M token

Output: ~$3 / 1M token

Claude Haiku 4.5 (veloce)
Input: $1 / 1M token
Output: $5 / 1M token
Claude Sonnet 4.6 (bilanciato, il più usato)
Input: $3 / 1M token
Output: $15 / 1M token
Claude Opus 4.6 (più capace)
Input: $5 / 1M token
Output: $25 / 1M token

EDIT:
mandato tutto tramite email a roberto','done',0,'2026-03-20T08:13:33.674028');
INSERT INTO "tasks" VALUES(63,2,'controllare gli esiti negativi del logging','EDIT:
non ha senso guardare gli esiti negativi, siccome la chiamata a AI è essa stessa la chiamata che genera gli scenari e di conseguenza non puo mai fallire un singolo scenario','done',1,'2026-03-20T08:16:03.550252');
INSERT INTO "tasks" VALUES(64,4,'Definire stack tecnologico','Decidere le tecnologie da usare: framework frontend (es. Next.js), backend/database (es. Supabase), hosting (es. Vercel).','done',0,'2026-03-20T11:28:31.581826');
INSERT INTO "tasks" VALUES(65,4,'Creare repository GitHub','','done',7,'2026-03-20T11:28:31.911452');
INSERT INTO "tasks" VALUES(66,4,'Inizializzare progetto','','done',1,'2026-03-20T11:28:32.149876');
INSERT INTO "tasks" VALUES(67,4,'Configurare variabili d''ambiente','','done',2,'2026-03-20T11:28:32.253413');
INSERT INTO "tasks" VALUES(68,4,'Definire struttura cartelle progetto','','done',3,'2026-03-20T11:28:32.490449');
INSERT INTO "tasks" VALUES(69,4,'Progettare tabelle database','Tabelle principali: utenti, ruoli, schede, esercizi, assegnazioni, sessioni di allenamento, log delle serie.','done',4,'2026-03-20T11:28:32.585039');
INSERT INTO "tasks" VALUES(70,4,'Implementare login e registrazione','Gestione dei due ruoli: Coach e Cliente.','done',5,'2026-03-20T11:28:32.837586');
INSERT INTO "tasks" VALUES(71,4,'Implementare protezione route per ruolo','','todo',0,'2026-03-20T11:28:32.914766');
INSERT INTO "tasks" VALUES(72,4,'Sviluppare Dashboard Coach','Pagina principale del coach con visione d''insieme: lista clienti, attività recente, chi non si allena da tempo.','done',6,'2026-03-20T11:28:33.182752');
INSERT INTO "tasks" VALUES(73,4,'Implementare invito clienti via email','','todo',1,'2026-03-20T11:28:33.248316');
INSERT INTO "tasks" VALUES(74,4,'Sviluppare lista clienti','','todo',2,'2026-03-20T11:28:33.517377');
INSERT INTO "tasks" VALUES(75,4,'Implementare rimozione/archiviazione clienti','','todo',3,'2026-03-20T11:28:33.586155');
INSERT INTO "tasks" VALUES(76,4,'Sviluppare gestione libreria esercizi','Il coach crea e gestisce la sua libreria personale di esercizi con nome, descrizione, muscoli coinvolti e link video YouTube.','done',11,'2026-03-20T11:28:33.857457');
INSERT INTO "tasks" VALUES(77,4,'Sviluppare creazione schede di allenamento','Il coach crea schede strutturate per giorni/sessioni, aggiungendo esercizi dalla libreria con serie, ripetizioni e note.','done',8,'2026-03-20T11:28:33.915482');
INSERT INTO "tasks" VALUES(78,4,'Implementare salvataggio schede come template','Il coach può salvare una scheda come template e riusarla per altri clienti con modifiche rapide.','done',9,'2026-03-20T11:28:34.184979');
INSERT INTO "tasks" VALUES(79,4,'Sviluppare assegnazione schede ai clienti','Il coach assegna una o più schede a un cliente specifico, con data di inizio e fine opzionale.','done',10,'2026-03-20T11:28:34.247904');
INSERT INTO "tasks" VALUES(80,4,'Sviluppare Dashboard Analytics Coach','Statistiche su tutti i clienti: frequenza di allenamento, progressioni, chi è a rischio abbandono.','todo',6,'2026-03-20T11:28:34.532985');
INSERT INTO "tasks" VALUES(81,4,'Sviluppare Dashboard Cliente','Pagina principale del cliente con la scheda attiva del giorno, ultimo allenamento e progressi recenti.','todo',7,'2026-03-20T11:28:34.582088');
INSERT INTO "tasks" VALUES(82,4,'Sviluppare visualizzazione scheda assegnata','Il cliente vede la scheda del coach in modo chiaro: esercizi del giorno, serie previste, note del coach.','todo',8,'2026-03-20T11:28:34.872466');
INSERT INTO "tasks" VALUES(83,4,'Sviluppare Workout Logger','Interfaccia rapida per inserire peso e ripetizioni per ogni serie durante l''allenamento.','todo',9,'2026-03-20T11:28:34.914894');
INSERT INTO "tasks" VALUES(84,4,'Implementare Timer di recupero','Timer integrato nel logger che parte automaticamente dopo ogni serie completata.','todo',10,'2026-03-20T11:28:35.202261');
INSERT INTO "tasks" VALUES(85,4,'Sviluppare storico allenamenti cliente','Il cliente può scorrere tutti gli allenamenti passati con i relativi log.','todo',11,'2026-03-20T11:28:35.249615');
INSERT INTO "tasks" VALUES(86,4,'Sviluppare grafici di progressione per esercizio','Es. peso massimo nel tempo, volume totale.','todo',12,'2026-03-20T11:28:35.534872');
INSERT INTO "tasks" VALUES(87,4,'Sviluppare grafici di progressione generali','Es. frequenza settimanale.','todo',13,'2026-03-20T11:28:35.582777');
INSERT INTO "tasks" VALUES(88,4,'Sviluppare sezione misurazioni corporee','Il cliente logga peso corporeo, circonferenze ecc. con grafico nel tempo.','todo',14,'2026-03-20T11:28:35.868954');
INSERT INTO "tasks" VALUES(89,4,'Implementare caricamento foto progressi','Il cliente carica foto periodiche visibili solo a lui e al coach.','todo',15,'2026-03-20T11:28:35.916846');
INSERT INTO "tasks" VALUES(90,4,'Sviluppare Check-in settimanale cliente','Questionario rapido settimanale (energia, sonno, stress, motivazione) visibile al coach nella sua dashboard.','todo',16,'2026-03-20T11:28:36.204901');
INSERT INTO "tasks" VALUES(91,4,'Sviluppare chat interna coach-cliente','Chat semplice tra coach e singolo cliente, con notifica di nuovo messaggio.','todo',17,'2026-03-20T11:28:36.238656');
INSERT INTO "tasks" VALUES(92,4,'Sviluppare sistema notifiche in-app','Notifiche per: nuova scheda assegnata, messaggio ricevuto, check-in da completare, cliente inattivo (lato coach).','todo',18,'2026-03-20T11:28:36.539285');
INSERT INTO "tasks" VALUES(93,4,'Definire piani di abbonamento','Definire i tier (es. fino a 5 clienti, fino a 20, illimitati) e i relativi prezzi mensili.','todo',19,'2026-03-20T11:28:36.570939');
INSERT INTO "tasks" VALUES(94,4,'Integrare Stripe per gestione abbonamenti','Implementare Stripe per la gestione degli abbonamenti ricorrenti del coach, con upgrade/downgrade piano.','todo',20,'2026-03-20T11:28:36.903566');
INSERT INTO "tasks" VALUES(95,4,'Sviluppare pagina di pricing pubblica','Landing page pubblica con presentazione dell''app, feature principali e piani di abbonamento.','todo',21,'2026-03-20T11:28:37.157150');
INSERT INTO "tasks" VALUES(96,4,'Implementare export scheda in PDF','Il coach può esportare una scheda allenamento in PDF da mandare o stampare.','todo',22,'2026-03-20T11:28:37.238564');
INSERT INTO "tasks" VALUES(97,4,'Eseguire testing su dispositivi reali','Testare l''intera app su iOS e Android in condizioni reali (in palestra, con una mano sola, ecc.).','todo',23,'2026-03-20T11:28:37.506656');
INSERT INTO "tasks" VALUES(98,4,'Configurare PWA per installabilità mobile','Configurare la webapp come Progressive Web App in modo che si possa installare sulla home del telefono.','todo',24,'2026-03-20T11:28:37.586007');
INSERT INTO "tasks" VALUES(99,4,'Redigere Privacy Policy e Cookie Policy','Conformi al GDPR.','todo',25,'2026-03-20T11:28:37.842348');
INSERT INTO "tasks" VALUES(100,4,'Redigere Termini di Servizio','Conformi al GDPR.','todo',26,'2026-03-20T11:28:37.922023');
INSERT INTO "tasks" VALUES(101,4,'Pianificare onboarding primi coach beta','Trovare 5-10 coach disposti a testare l''app gratuitamente in cambio di feedback dettagliato.','todo',27,'2026-03-20T11:28:38.181339');
INSERT INTO "tasks" VALUES(102,4,'mettere nelle note tutte le info necessarie per tirare giu l''ambiente su un altro pc','','in_progress',0,'2026-03-20T15:02:23.856575');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('projects',4);
INSERT INTO "sqlite_sequence" VALUES('tasks',102);
INSERT INTO "sqlite_sequence" VALUES('labels',4);
INSERT INTO "sqlite_sequence" VALUES('project_files',3);
COMMIT;