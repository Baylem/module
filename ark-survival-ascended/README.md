# `ark-survival-ascended` module

Gameplane GameTemplate for ARK: Survival Ascended dedicated servers.

## Install

```sh
kubectl apply -f modules/ark-survival-ascended/template.yaml
```

## Image

[`mschnitzer/asa-linux-server`](https://github.com/mschnitzer/ark-survival-ascended-linux-container-image) —
a native-Linux (Proton) ASA server image with an `asa-ctrl` RCON helper.
This replaces the previous draft's `thmhoag/arkserver`, which targets the
older ARK: Survival Evolved (not Ascended) and has been archived since
2023.

## Launch parameters

Map, listen port, RCON, and player count are one combined launch string
on this image, not discrete env vars — the **Launch parameters** field
passes it straight through, e.g.
`TheIsland_WP?listen?Port=7777?RCONPort=27020?RCONEnabled=True
-WinLiveMaxPlayers=70` (map + `?query=params`, then space-separated
`-Flag=value` args — matches the image's own documented example).
**Do not** put `ServerAdminPassword` in this field: the image's own docs
warn against setting it on the command line. Set it via the wizard's
**Admin / RCON password** field instead (see Console & RCON below for the
one-time step needed to make it take effect).

## Console & RCON

ASA's RCON is genuine Source-RCON-protocol — mcrcon, BattleMetrics, and
this image's own `asa-ctrl` tool all work against it unmodified, on the
image's own canonical port, **27020** (no `consoleMode` is set, so it
defaults to `rcon`).

**`GameUserSettings.ini` is not managed by this template.** ASA owns and
rewrites that file wholesale — every setting an admin tunes in-game
(difficulty, taming rates, structure limits, ...) persists there.
Gameplane's config-init copies rendered `configFiles` onto the data
volume on *every* pod start, so if this template rendered
`GameUserSettings.ini` the way an earlier draft did, all of that would be
silently wiped on the next restart. Instead, the wizard's **Admin / RCON
password** field only renders into a Gameplane-owned `rcon-password.txt`
(a file ASA never reads) that the agent uses for its own RCON connection
attempts — always safe to re-render, since ASA doesn't touch it.

**One-time setup required.** For RCON to actually authenticate, add the
following to the `[ServerSettings]` section of
`server-files/ShooterGame/Saved/Config/WindowsServer/GameUserSettings.ini`
via the **Files** tab (once, after the first boot), matching the wizard's
Admin / RCON password field exactly:

```
RCONEnabled=True
ServerAdminPassword=<same value as the wizard's Admin / RCON password field>
RCONPort=27020
```

If you change the password field later, repeat this step — Gameplane
won't touch the file for you again. This is the same one-time-bootstrap
pattern the `cs2` module uses for Metamod: a thing the game owns that
Gameplane sets up once via the Files tab instead of every restart.

## Server name

ASA generates a random `SessionName` (under `[SessionSettings]` in
`GameUserSettings.ini`) on first boot. For the same reason there's no
managed RCON password rendering, there's no wizard field for the server
name either — rename the server by editing `SessionName` there directly
via the Files tab.

## Mods

CurseForge mods are managed via the **Mods** tab in the dashboard. Select
mods to install them — the game downloads them itself at boot via the
`-mods=<id>,<id>` launch parameter, which is automatically appended to
your **Launch parameters** string. The manual-unzip `.../Mods/<id>` layout
only applies to the singleplayer/manual flow, not the dedicated-server
flow this image runs.

## Ports

| Name  | Port  | Protocol | Advertised |
| ----- | ----- | -------- | ---------- |
| game  | 7777  | UDP      | yes        |
| peer  | 7778  | UDP      | yes        |
| rcon  | 27020 | TCP      | no         |

There is no query port: the image's own README states plainly that "ASA
does no longer offer a way to query the server" — the game is only
discoverable via the in-game server browser, not Steam's server-query
protocol.

## Storage

The image documents four separate Docker volumes (Steam cache, SteamCMD
cache, server-files, cluster-shared) with no common parent besides
`/home/gameserver` — this template mounts that whole directory as one
PVC so nothing is silently lost on restart. `server-files/` is what
actually holds saves and `GameUserSettings.ini`. Default size is 30 GiB;
ASA's base install alone is roughly 11 GiB, so heavy mod/save usage may
need more.

## Backups

**Save world** runs `SaveWorld`. ARK can change world and player files again
while a live backup is copying them. For a stopped copy, shut down the server,
wait for it to stop, then request a backup with quiesce enabled. Keep the
server stopped until the backup completes.

## Known limitations

- `SaveWorld`/`DoExit` and `ServerChat` are corroborated by community
  guides and the image's own `asa-ctrl` example, not an official Studio
  Wildcard reference — there is no first-party ARK:SA RCON command
  documentation.
- Resource requests/limits (10Gi/20Gi memory) follow community sizing
  guidance rather than an official minimum; ASA is markedly heavier than
  ARK: Survival Evolved.
- RCON and the server name both require a one-time manual edit to
  `GameUserSettings.ini` via the Files tab (see Console & RCON / Server
  name above) — Gameplane can't safely automate either without risking
  wiping other in-game-tuned settings on the next restart.

## Sample

See [`samples/gameserver.yaml`](samples/gameserver.yaml) for an example deployment manifest.
