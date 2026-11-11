# `project-zomboid` module

Gameplane GameTemplate for Project Zomboid dedicated servers.

## Install

```sh
kubectl apply -f modules/project-zomboid/template.yaml
```

## Image

[`sknnr/zomboid-dedicated-server`](https://github.com/jsknnr/project-zomboid-server).

## Console & RCON

Project Zomboid's RCON is genuine Source-RCON-protocol — every actively
maintained RCON client library that supports PZ implements the plain
Source wire protocol with no special-casing. The **Console** tab, player
moderation (kick/ban), and the **Save world** action all ride this
connection (no `consoleMode` is set, so it defaults to `rcon`).

## Mods

Workshop mods are entirely config-driven: the game's own SteamCMD sync
downloads whatever is listed in **Workshop item IDs**, and **Mod IDs**
(the corresponding internal `mod.info` IDs, same order) activates them.
Both fields are required together — a Workshop item with no matching Mod
ID downloads but never loads. There is no panel-managed mods folder for
this game (no `capabilities.mods` block): Workshop content is entirely
game-managed via these two config fields, not files an admin drops in.

## Ports

| Name   | Port  | Protocol | Advertised |
| ------ | ----- | -------- | ---------- |
| game   | 16261 | UDP      | yes        |
| direct | 16262 | UDP      | yes        |
| rcon   | 27015 | TCP      | no         |

RCON is a separate port from the game port (unlike CS2/GMod), running on
PZ's canonical default, **27015**.

## Storage

The PVC mounts at `/home/steam/Zomboid`, covering the persistent world and configuration data.
Default size is 15 GiB — heavy Workshop mod usage may need more.

## Backups

`AUTOSAVE_INTERVAL` controls periodic saves. **Save world** forces an
immediate save. Project Zomboid can write map chunks and player data during
a live backup. For a stopped copy, shut down the server, wait for it to stop,
then request a backup with quiesce enabled. Keep the server stopped until the
backup completes. Use the Gameplane Backup CRD to request the copy. The
image also supports `BACKUPS_PERIOD` and `BACKUPS_COUNT` outside this template.

## Sample

See [`samples/gameserver.yaml`](samples/gameserver.yaml) for an example deployment manifest.
