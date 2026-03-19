# Transformative Content Framework - PeanutClip AutoFlow

Status: Draft  
Datum: 17 maart 2026

## Doel

Definieer hoe het systeem clips produceert die authentiek en origineel zijn, in lijn met YouTube reused-content eisen voor transformatieve output.

## 1. Kernprincipe

Een clip is alleen publiceerbaar als deze een nieuwe creatieve bewerking vormt en niet slechts een grab of minimale cut van bronmateriaal.

## 2. Creatieve bouwstenen per clip

Elke clip moet minimaal 4 van de 6 bouwstenen bevatten:

1. Hook layer
- Eerste 1-2 seconden met sterke hooktekst.
- Hooktekst wordt gekozen uit een trendset en aangepast op context.

2. Dynamic caption layer
- Woord-voor-woord of phrase-voor-phrase captions met nadruk op punchwoorden.
- Captionstijl wisselt per clipset om repetitie te verminderen.

3. Motion edit layer
- Minimaal 1 actieve beweging: speed ramp, micro-zoom, punch-in, of whip pan.

4. Transition layer
- Minimaal 1 transition uit een roterende trendbibliotheek.
- Geen exact dezelfde transitionvolgorde in opeenvolgende clips.

5. Context layer
- Korte extra context: titelkaart, callout, mini-reactieframe, of setup-lijn.

6. Brand layer
- Fan-account branding met subtiele vaste signatuur (kleur, bug, endcard).

## 3. Trend engine

De trend engine beheert captions en transitions als versioned presets.

Inputbronnen (periodiek):
- Interne performance data (retentie, completion rate, shares)
- Handmatige trendcuratie door beheerder

Output:
- Caption Pack vN
- Transition Pack vN
- Hook Pattern Pack vN

Regels:
- Elke pack heeft startdatum, einddatum, owner en performance-score.
- Slecht presterende packs worden automatisch uitgefaseerd.
- Prestaties worden beoordeeld op basis van post-performance windows, niet alleen op subjectieve review.

Extra packs:
- Font Pack vN
- Animation Pack vN

## 4. Variatie en anti-repetitie

Anti-repetitieregels binnen rolling window van 30 clips:

- Max 3 keer exact dezelfde hook-template.
- Max 2 keer exact dezelfde transitionketen.
- Geen identieke caption-styling op meer dan 20% van clips.
- Minimaal 3 verschillende edit-routes per 10 clips.
- Maximaal 40% van output mag uit exact dezelfde font-pack komen in rolling window van 30 clips.
- Minimaal 20% van output reserveert ruimte voor experimenten met nieuwe fonts, transitions of animations.

Edit-routes (voorbeeld):
- Route A: Hook -> Punch captions -> Zoom cuts -> Endcard
- Route B: Cold open -> Speed ramp -> Pop captions -> CTA
- Route C: Setup card -> Dialog highlight -> Whip transition -> Reaction end

## 5. Authenticity Score (publish gate)

Elke clip krijgt een score van 0-100.

Componenten:
- Transform depth (0-35): hoeveelheid en impact van edits
- Visual originality (0-20): mate van nieuwe visuele laag
- Narrative reframing (0-20): nieuwe hook/context structuur
- Template uniqueness (0-15): afwijking van recente output
- Compliance confidence (0-10): rechten- en policychecks compleet

Publish gate:
- Score >= 70: klaar voor review en scheduling
- Score 55-69: revise queue (extra edit vereist)
- Score < 55: reject

Hard fails (altijd reject):
- Geen rights-check
- Alleen ruwe trim zonder creatieve lagen
- Repetitie boven ingestelde limieten

Opmerking:
- Hoge performance mag nooit een clip door de gate trekken als authenticiteit of compliance faalt.

## 6. Human review checklist

Reviewer keurt clip alleen goed als alle punten true zijn:

- Clip voelt als nieuwe edit, niet als raw herupload
- Hook en captions verhogen begrijpelijkheid/entertainment
- Transitions ondersteunen ritme en leiden niet af
- Branding is fan-achtig en niet misleidend als officieel account
- Rights status en source metadata zijn compleet

## 7. Data die per clip opgeslagen moet worden

- source_channel_id
- source_video_id
- source_time_range
- applied_caption_pack_version
- applied_font_pack_version
- applied_transition_pack_version
- applied_animation_pack_version
- applied_edit_route
- authenticity_score
- reviewer_decision
- publish_platforms

## 8. Learning loop voor creatieve optimalisatie

Per gepubliceerde clip bewaart het systeem:

- 1h performance snapshot
- 24h performance snapshot
- 48h performance snapshot
- normalized performance score
- experiment flag
- winning/losing variable attribution

De learning loop gebruikt deze data om:

- hook packs te her-ranken
- fonts te her-ranken
- transition packs te her-ranken
- animation packs te her-ranken
- duur- en timingvoorkeuren per platform te her-ranken

## 9. Experimentregels

- 70-80% van clips gebruikt bewezen creatieve combinaties.
- 20-30% van clips test nieuwe combinaties.
- Experimenten mogen slechts 1-2 hoofdelementen tegelijk wijzigen om causale interpretatie bruikbaar te houden.
- Verlieslatende experimenten worden automatisch uitgefaseerd na ingestelde drempel.

## 10. MVP implementatievolgorde

1. Caption pack systeem met 3 stijlen
2. Transition pack systeem met 5 transitions
3. Authenticity scoring met basisheuristieken
4. Human review UI met approve/revise/reject
5. Font en animation packs als testbare variabelen
6. Trend pack rotatie op basis van prestaties
7. Basis recommendation loop op post-performance

## 11. Niet-doen lijst

- Geen massale batch-publicatie zonder review
- Geen volledig identieke templates op alle clips
- Geen impliciete claim dat account officieel van creator is
- Geen publicatie als rights-check ontbreekt