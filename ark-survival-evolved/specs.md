# Gameplane Module Specification: ARK: Survival Evolved

## 1. Purpose & Scope

- **Game**: ARK: Survival Evolved
- **Module Slug**: `ark-survival-evolved`
- **Role**: Dedicated server module package for Gameplane.
- **Description**: Dedicated multiplayer server for Studio Wildcard's ARK: Survival Evolved. Manages persistent world saves, multi-shard cluster transfers, and Source RCON administration.

---

## 2. Container Image & Architecture

- **Base Image**: `hermsi/ark-server:latest@sha256:ce291990613e76f7019be31b96fe247188ce4957724c913c0e30097042c44bf5`
- **Architecture**: `linux/amd64`
- **Image Source**: Community image from https://github.com/Hermsi1337/docker-ark-server, rebuilt weekly on `cm2network/steamcmd`. Chosen over a Gameplane-built image on 2026-11-11 (maintainer ruling: use a maintained public image when one exists).
- **Runtime Model**: SteamCMD Linux dedicated server (`ShooterGameServer`), installed, updated and run by arkmanager (`arkmanager run`).
- **User & Execution Context**: Starts as root, then drops to `steam` (UID/GID 1000) with gosu. Working directory `/app`.

---

## 3. Network Ports & Protocols

Declared ports under `spec.ports`:

| Port Name | Container Port | Protocol | Usage / Purpose |
|---|---|---|---|
| `game` | 7777 | UDP | Primary gameplay traffic |
| `raw` | 7778 | UDP | Raw UDP socket, always game port + 1 |
| `query` | 27015 | UDP | Steam A2S browser discovery |
| `rcon` | 27020 | TCP | Remote administrative console (Source RCON) |

---

## 4. Storage & Persistence Layout

- **Mount Path**: `/app` (the image's declared volume)
- **Default Sizing**: `35Gi`
- **Persisted Content**:
  - Game install (`/app/server`)
  - Saved worlds, tribe data, and dinosaur entities (`/app/server/ShooterGame/Saved/SavedArks/`)
  - Server configuration files (`/app/server/ShooterGame/Saved/Config/LinuxServer/GameUserSettings.ini`)
  - arkmanager configuration, logs and update staging (`/app/arkmanager`, `/app/log`, `/app/staging`)
- **Extra Volume**: `cluster`, `1Gi`, mounted at `/cluster` for cross-server cluster transfers (the image sets `-ClusterDirOverride=/cluster` when `CLUSTER_ID` is set).
- **Non-Shadowing Invariant**: The image's entrypoints live in `/`, outside both mounts, and `/app` holds no baked game content.

---

## 5. Administration & Remote Console (RCON)

- **Protocol**: `source`
- **Console Mode**: `rcon`
- **Authentication**: The operator-generated password is supplied via `ADMIN_PASSWORD` (`rcon.passwordEnv`), which arkmanager writes as `ServerAdminPassword` with `RCONEnabled=True`.
- **Command Support**: In-game moderation (`KickPlayer`, `BanPlayer`), world saving (`SaveWorld`), broadcasts (`ServerChat`).

---

## 6. Modding & Workshop Integration

- **Modding Framework**: Steam Workshop (`-automanagedmods`).
- **Mod Directory Path**: Managed within image install.

---

## 7. Lifecycle & Graceful Shutdown

- **Stop Command Sequence (`spec.capabilities.lifecycle.stop`)**:
  ```yaml
  capabilities:
    lifecycle:
      stop:
        - "SaveWorld"
        - "DoExit"
  ```
- **Signal Handling**: The image traps `SIGTERM`/`SIGINT` and stops the server through arkmanager, which saves first.
- **1.x migration**: Before the image starts, the game container checks the primary and cluster mount points, the 1.0 Saved-only layout, the 1.1 install layout and transfer files left under `server/ShooterGame/Saved/clusters`. On failure it exits 78 with a recovery message. It hands PID 1 to the pinned vendor entrypoint after these checks pass.

---

## 8. Key Invariants & Security

- **No runAsUser**: the image must start as root so its entrypoint can drop to `steam`. It therefore cannot run with the operator's restricted workloads enabled.
- **Filesystem Permissions**: `spec.security.fsGroup: 1000` gives the dropped `steam` user write access to both volumes.
- **Image Defaults Overridden in `spec.env`**: `SERVER_PASSWORD=""` (the image default is `YouShallNotPass`), `UPDATE_ON_START=true` (update on every start, as 1.x did), `PRE_UPDATE_BACKUP=false` (Gameplane runs its own backups), and the four port variables.

---

## 9. References & Upstream Documentation

- ARK: Survival Evolved Dedicated Server: https://ark.wiki.gg/wiki/Dedicated_server_setup
- Steam Dedicated Server AppID: 376030
