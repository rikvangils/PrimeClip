# Product Brief – PeanutClip AutoFlow

> **Status:** Concept | **Datum:** 17 maart 2026 | **Auteur:** Rik

---

## 1. Probleemstelling

_Welk probleem los je op? Voor wie?_

Fan-accounts die clips maken van populaire streamers verliezen veel tijd aan handmatig zoeken, knippen en posten.
Daardoor is de doorlooptijd te traag en worden trends vaak gemist.
Dit project lost dat op door automatisch nieuwste content van theburntpeanut te detecteren, de grappigste momenten te selecteren en publicatie naar social kanalen te plannen.

---

## 2. Doelgroep

_Wie zijn de primaire gebruikers?_

Primaire gebruiker is 1 beheerder van een fan-content account rond theburntpeanut.
Context: dagelijkse contentproductie voor korte video platforms.
Pijnpunten: handmatige monitoring van YouTube uploads, tijdrovende clipselectie en inconsistente posting-frequentie.

---

## 3. Oplossingsrichting

_Wat is jouw idee op hoog niveau?_

Het systeem monitort het YouTube-kanaal van theburntpeanut op nieuwe uploads (video of stream VOD).
Bij detectie wordt de video automatisch gedownload of gestreamd voor analyse.
Een pipeline detecteert high-energy/grappige segmenten op basis van audio-intensiteit, gelach/reactiepatronen, transcript-signalen en scènewisselingen.
De beste segmenten worden automatisch geknipt, ondertiteld en geformatteerd in verticale short-form clips.
Vervolgens worden clips gratis/open-source-first ingepland via een lokale publish queue of native gratis API-flow voor TikTok en Instagram op een fan-account, met menselijke review-optie vóór publicatie.

---

## 4. Kernwaarde & differentiatie

_Waarom is jouw oplossing beter of anders dan wat er al bestaat?_

- Single-source focus: geoptimaliseerd voor contentstijl van theburntpeanut in plaats van generieke clipping.
- Near-real-time: snelle verwerking direct na upload van nieuwe YouTube content.
- End-to-end flow: van detectie tot scheduling zonder verplichte betaalde tooling; standaard via lokale/manual publish queue of gratis/native integraties.
- Consistente output: vaste templates voor captioning, aspect ratio en branding van fan-account.
- Transformatieve creatie: output is een nieuwe edit met eigen ritme, captions, structuur en visuele stijl.

---

## 5. Succes-criteria (KPI's)

_Hoe weet je of het werkt?_

- Nieuwe upload wordt binnen 10 minuten gedetecteerd in 95% van de gevallen.
- Eerste batch clips staat binnen 45 minuten klaar voor review/publicatie.
- Minimaal 5 publiceerbare clips per nieuwe lange video/stream.
- Minimaal 90% van ingeplande posts wordt zonder handmatige herwerking gepubliceerd.
- Minimaal 95% van gepubliceerde clips haalt interne transformatieve kwaliteitsdrempel (Authenticity Score).
- Maximaal 10% van gepubliceerde clips gebruikt exact dezelfde caption/transition-combinatie als eerdere clips.

---

## 6. Scope (Fase 1 – MVP)

**In scope:**
- Monitoring van enkel het YouTube-kanaal van theburntpeanut.
- Automatische extractie van topfragmenten op basis van scoremodel.
- Verticale clip rendering (9:16) met basis ondertiteling.
- Gratis/self-hosted publish queue of gratis/native schedulingflow naar TikTok en Instagram.
- Handmatige approve/reject stap vóór definitieve scheduling.
- Trendgedreven captioning en hook-overlays met periodieke update van templates.
- Unieke transition packs en edit-patronen per clip om repetitieve output te vermijden.
- Authenticity gate: automatische reject van clips die te dicht op bronmateriaal blijven zonder voldoende creatieve bewerking.

**Buiten scope:**
- Multi-creator ondersteuning.
- Direct posten zonder review.
- Geavanceerde generatieve edits (AI voice-over, deepfake, etc.).
- Volledig autonome engagement-optimalisatie per platform.

---

## 7. Technologische overwegingen (optioneel)

- Integraties: YouTube Data API, gratis/native platform-API's waar beschikbaar, en anders lokale/self-hosted publish queue.
- Pipeline: Python/Node worker voor ingest + analyse + clipping.
- Video tooling: ffmpeg voor cutting, reframing en rendering.
- Analyse: transcriptie + heuristische scorelaag + optioneel ML-rankingmodel.
- Opslag: object storage voor bronvideo, clips en metadata.
- Orchestratie: scheduled job + event queue voor robuuste verwerking.

---

## 8. Open vragen

- Publicatie-rechten: is expliciete toestemming aanwezig om clips van theburntpeanut te herpubliceren op fan-kanalen?
- Platform-policy: welke gratis/native publicatief low is haalbaar per doelkanaal en accounttype?
- Reviewflow: wil je webdashboard, Discord approval, of eenvoudige CLI/Notion queue?
- Frequentie: hoeveel clips per upload zijn gewenst per platform?
- Tone of voice: vaste captionstijl/hashtags of dynamisch gegenereerd?

---

## 9. Compliance & randvoorwaarden

- Alleen content gebruiken waarvoor je rechten/permission hebt om te knippen en te herpubliceren.
- Fan-account moet transparant zijn (geen impersonatie van officiële creator-account).
- Respecteer YouTube, TikTok en Instagram Terms of Service.

## 9b. Tooling-constraint

- Nieuwe onderdelen moeten gratis, open-source of self-hosted zijn waar redelijkerwijs mogelijk.
- Betaalde SaaS-tools zijn niet toegestaan als verplichte productafhankelijkheid.
- Eventuele bestaande Buffer-adapter blijft optioneel/legacy en niet leidend voor volgende implementatiestappen.
- Voeg een hard filter toe zodat alleen content van theburntpeanut wordt verwerkt (kanaal-ID whitelisting).
- Niet publiceren als clip onvoldoende transformatief is volgens interne kwaliteitsregels voor originele bewerking.

---

## 10. Transformatieve content standaard

Elke clip moet aantoonbaar een nieuwe creatie zijn en niet alleen een directe extractie.

Minimale vereisten per clip:

- Nieuwe narratieve structuur: duidelijke hook, payoff en einde.
- Dynamische captions: stijl die afwijkt van standaard auto-subtitles (highlight-woorden, timing op beat, hooktekst).
- Minimaal 2 creatieve edits: bijvoorbeeld reframing + transition, of transition + speed-ramp.
- Merkbare contextlaag: titelkaart, reaction frame, callout of korte duiding.
- Variatie-eis: geen identieke template-combinatie binnen recente publicaties.

---

_Vul dit bestand in samen met GitHub Copilot: zeg "lets create a product brief" om het interactieve BMAD-proces te starten._
