# Domain Research - YouTube clip channels, rechten en monetization

Status: Draft  
Datum: 17 maart 2026

## Onderzoeksvraag

Waarom kunnen videos die clips maken van een andere creator (zoals TheBurntPeanut) op YouTube blijven staan en soms inkomsten genereren?

## Onderzocht voorbeeld

- Video: The BEST clips of TheBurntPeanut... SO FAR
- Publieke metadata (oEmbed): kanaal Burnt Peanut After Dark
- URL: https://www.youtube.com/watch?v=LyKddtSKzXo

Opmerking: de exacte monetization-status van een individuele video is meestal niet publiek verifieerbaar.

## Belangrijkste bevindingen

### 1) Content ID bepaalt vaak of een clip online blijft

Volgens YouTube kan een Content ID match leiden tot drie uitkomsten:

- block (video niet zichtbaar)
- monetize (ads op video, soms met revenue share)
- track (alleen volgen)

Conclusie: als rechthebbende policy op monetize of track staat, kan een clipvideo online blijven.

Bron:
- https://support.google.com/youtube/answer/2797370
- https://support.google.com/youtube/answer/6013276

### 2) Online blijven betekent niet automatisch dat uploader rechten heeft

Een video kan zichtbaar blijven omdat de rechthebbende nog niet heeft gehandhaafd, of bewust monetization/track toelaat via Content ID.

Conclusie: zichtbaarheid is geen juridisch bewijs van toestemming.

Bron:
- https://support.google.com/youtube/answer/6013276

### 3) Monetization in YPP vereist originele en authentieke bewerking

YouTube monetization policy vereist dat geleende content significant wordt veranderd en niet mass-produced of repetitief is. YouTube noemt expliciet dat reused-content review ook kijkt naar clips, compilaties en reaction-videos.

Conclusie: clipkanalen kunnen monetizable zijn als output voldoende transformatief en authentiek is.

Bron:
- https://support.google.com/youtube/answer/1311392

### 4) Fair use is context-afhankelijk en door rechter te bepalen

YouTube geeft aan dat fair use geen automatische bescherming is; uiteindelijke beoordeling gebeurt juridisch per case.

Conclusie: fair use kan relevant zijn, maar is geen veilige operationele basis zonder risicobeheersing.

Bron:
- https://support.google.com/youtube/answer/9783148

## Waarom dit soort videos dus vaak blijven bestaan

Combinatie van factoren:

- Rechthebbende laat gebruik toe via Content ID policy (track/monetize)
- Rechthebbende handhaaft niet direct of niet in alle regio's
- Video wordt gezien als voldoende transformatief (commentaar, edit, context)
- Er bestaat mogelijk expliciete of impliciete toestemming van creator/management

## Relevantie voor PeanutClip AutoFlow

Voor jouw systeem (fan-account, alleen theburntpeanut) betekent dit:

- Juridisch/operationeel het veiligst met expliciete toestemming/licentie van theburntpeanut of rechtenhouder.
- Bouw een rights-first gating stap: zonder bevestigde rechten geen auto-publish.
- Houd menselijke review op elke clip voor transformatieve kwaliteit en policy-risico.
- Gebruik transparante fan-branding (geen impersonatie van official account).

## Praktisch advies voor fase 1

- Start met semi-automatisch: auto-detect + auto-clip + manual approve.
- Publiceer pas na rights-check per kanaal.
- Bewaar provenance metadata per clip:
  - source video id
  - gebruikte timestamps
  - bewerkingen (captions, crop, overlays)
  - approval log

Dit maakt bezwaarafhandeling en policy-review veel eenvoudiger.