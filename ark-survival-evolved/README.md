# ARK: Survival Evolved

ARK: Survival Evolved dedicated server package for Gameplane. Runs on Linux with persistent world state, Steam A2S server browser discovery, Source RCON console, and multi-server cluster transfer support.

The module runs the community image [`hermsi/ark-server`](https://github.com/Hermsi1337/docker-ark-server), pinned by digest. The image installs and updates the server with SteamCMD on start and runs it under [arkmanager](https://github.com/arkmanager/ark-server-tools).

## Install

```sh
kubectl apply -f modules/ark-survival-evolved/template.yaml
```

## Console & RCON

Remote management uses standard Source RCON on port 27020 TCP. The operator generates the password and injects it as `ADMIN_PASSWORD`, which the image uses as the server admin and RCON password. Console actions include `ServerChat` (broadcast), `SaveWorld` (world flush), and `KickPlayer` (moderation).

The server stops cleanly by issuing `SaveWorld` and `DoExit` prior to container termination.

## Ports

| Name | Port | Protocol | Advertised | Purpose |
| ---- | ---- | -------- | ---------- | ------- |
| `game` | 7777 | UDP | yes | Primary gameplay traffic |
| `raw` | 7778 | UDP | yes | Raw UDP socket (always game port + 1) |
| `query` | 27015 | UDP | yes | Steam A2S browser query |
| `rcon` | 27020 | TCP | no | Source RCON administration |

## Storage & Cluster Travel

The data volume is mounted at `/app` (35 GiB default). The game is installed in `/app/server` on first start, and map saves, tribe data and player profiles persist under `/app/server/ShooterGame/Saved`. arkmanager keeps its configuration in `/app/arkmanager` and its logs in `/app/log`.

Cluster transfer data (uploaded survivors, dinos and items) lives in a second 1 GiB volume at `/cluster`. To enable cluster travel between multiple ARK servers, supply the same `CLUSTER_ID` in each server's configuration and share or synchronize the `/cluster` folder.

## Security

The image starts as root and drops to the `steam` user (UID/GID 1000) in its entrypoint, so the template sets only `fsGroup: 1000`. It does not run when the operator enforces restricted workloads (`enforceRestricted: true`), which needs a non-root image.

## Upgrading from 1.x

Schedule downtime before adopting 2.x. Version 1.0 mounted the primary claim directly at `/serverdata/ShooterGame/Saved`. Version 1.1 mounted the whole install at `/data`. Version 2.x mounts the same claim at `/app` and reads `server/ShooterGame/Saved`. Starting 2.0.0 with either old layout can create a second world. Use 2.0.1 or later for the startup check.

1. Stop the GameServer and any other shard that writes these transfers. Wait for their game Pods to exit. Back up the primary PVC and any existing cluster PVC. Keep those backups until the world and transfers have been verified in game.
2. Mount the primary PVC at `/app` for maintenance. For a **1.0 Saved-only claim**, move its saved data, including `SavedArks` and `Config`, into `/app/server/ShooterGame/Saved`. For a **1.1 full-install claim**, move its install, including `ShooterGame`, `Engine` and `steamapps` if present, into `/app/server`. Preserve ownership and permissions. Verify the expected map, character profiles and tribes in the destination. If both layouts contain saves, compare them and choose the intended world before moving either.
3. Mount the cluster PVC at `/cluster`. Copy all old transfers, including hidden and nested files, from the 1.0 claim’s `clusters/` or the 1.1 install’s `ShooterGame/Saved/clusters/` to the matching paths on that PVC. Compare the source and destination contents. Archive the verified old transfers outside the live install. No `clusters/` directory should remain at `/app` or `/app/server`; the old `/app/server/ShooterGame/Saved/clusters` may contain empty directories.
4. Rename `MAP_NAME` to `SERVER_MAP` and remove `RCON_PASSWORD` from GameServer configuration. The operator manages the RCON password. Start the game, load the intended world and verify a known player or tribe and any cluster transfers before reopening it.

If the log or Kubernetes termination message begins with `ARK storage check`, keep the game stopped and inspect the named path. Version 2.0.1 checks both mounts before invoking the vendor entrypoint. A missing mount, old install, unreadable path, or residual cluster transfer blocks startup and leaves both volumes intact.

## Sample

See [`samples/gameserver.yaml`](samples/gameserver.yaml) for a deployment example.
