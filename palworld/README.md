# Palworld (Dedicated)

Palworld dedicated server backed by the community
[thijsvanloef/palworld-server-docker](https://github.com/thijsvanloef/palworld-server-docker)
image. The game server itself is installed and updated by **steamcmd at
container start** (`UPDATE_ON_BOOT=true`), so the game always tracks Steam.

> **First boot is slow.** steamcmd downloads several GB before anything
> listens. The template's startup probe budgets ~30 minutes; watch progress
> in the dashboard's Logs tab (source "pod").

## Version picker

The wizard's version picker selects the **wrapper image channel**, not the
game version (that always tracks Steam):

| Entry | Tag | Use when |
|---|---|---|
| Latest wrapper | `latest` | default; newest wrapper scripts |
| v2 wrapper | `v2` | follow the v2 major line only |
| v2.4.1 wrapper | `v2.4.1` | pin everything except the game itself |

## Console & admin

RCON is **deprecated** by Palworld upstream ("scheduled to stop functioning
in an upcoming update" per docs.palworldgame.com), so this module talks to
Palworld's **REST admin API** instead (port 8212). The operator generates a
per-server password and injects it as `ADMIN_PASSWORD`, which the image
uses for **both** the REST API and the in-game admin password — read it
from the `<server>-rcon` Secret if you need to `/AdminPassword` in game.

Graceful stop runs `save` then `shutdown 1` over the REST API, so the
server never takes a SIGTERM mid-save. Backups snapshot the data volume
directly (no quiesce — Palworld's `save` is a one-shot flush, not a
pausable state); freshness therefore rides the server's autosave interval,
and the "Save world" action forces a flush on demand.

**Players tab** shows who's online (`GET /v1/api/players`). There's no
kick/ban here, though: the REST API moderates by a player's `userId`
(e.g. `steam_12345`), a different field from the display name the Players
tab lists, and Gameplane only carries one value through that pipeline — so
a kick/ban button here would target the wrong (or no) account. Use the
in-game admin commands, or the REST API directly, for kick/ban.

**Quick actions**: Broadcast message, Save world, and Announce restart
(counts down, then shuts down cleanly) — see the server detail page's
Actions panel.

The Overview and Prometheus expose the dedicated server's frame rate from
`GET /v1/api/metrics` in frames per second. An observed zero is a valid
reading. Missing data, failed authentication and stale responses leave the
numeric series absent. The module sets no universal frame-rate threshold.
[Palworld REST metrics](https://docs.palworldgame.com/api/rest-api/metrics/)

## Mods (.pak)

The Mods tab manages engine-native **`.pak` mods** in
`Pal/Content/Paks/~mods` on the server volume:

- **From URL** — GitHub-hosted `.pak` files (the allowlist covers
  `github.com` and release/raw CDNs).
- **Upload** — push a locally built/downloaded `.pak` straight from the
  browser (Gameplane ≥ the release with mod uploads).

Server + client mod pairs generally require players to install the client
half themselves — that's inherent to Palworld modding, not the panel.

**UE4SS / Lua mods are not bundled.** UE4SS on Linux dedicated servers is
still experimental and needs files injected next to the game binary. If you
want to experiment, install it manually via the Files tab into
`Pal/Binaries/Linux/` per the UE4SS docs — at your own risk; updates from
steamcmd may clobber it.

## Sizing

Palworld is memory-hungry: the template requests 4Gi and caps at 12Gi/4
CPUs. Long-running servers with many pals benefit from more memory and the
image's `AUTO_REBOOT_*` options (set via the EnvVars settings tab).

## Sample

See [`samples/gameserver.yaml`](samples/gameserver.yaml) for a NodePort
deployment with a password and community listing disabled.
