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

Version 1.x ran a Gameplane-built image with the volume at `/data`. Version 2.0.0 changes three things:

- **Data layout.** The install and saves move from the volume root to `server/` inside it. Before you start an existing server on 2.0.0, stop it and move everything at the root of its data volume into a new `server/` subfolder. If you skip this, the server installs again and starts a new world.
- **Cluster data.** It moves from `ShooterGame/Saved/clusters` to the new `/cluster` volume. Copy the folder contents over if you use cluster travel.
- **Config keys.** `MAP_NAME` is now `SERVER_MAP`, and `RCON_PASSWORD` is gone because the operator manages the RCON password. Rename or remove those keys in each GameServer, or the operator rejects it as having unknown config keys.

## Sample

See [`samples/gameserver.yaml`](samples/gameserver.yaml) for a deployment example.
