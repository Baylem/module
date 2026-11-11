# Gameplane Module Specification: Palworld (Dedicated)

## 1. Purpose & Scope

- **Game**: Palworld
- **Module Slug**: `palworld`
- **Role**: Dedicated server module package for Gameplane.
- **Description**: Open-world survival crafting multiplayer server. Supports player progression, building, and Pal capture. Administered via native REST API (RCON is deprecated upstream).

---

## 2. Container Image & Architecture

- **Base Image**: `thijsvanloef/palworld-server-docker:latest@sha256:4145c58737fcd9f9f03d35de6bf33c0008b829b65d3080822bc46830bdb38fdf`
- **Architecture**: `linux/amd64`
- **Runtime Model**: Wrapper container that downloads and updates the Palworld Linux dedicated server files via SteamCMD at boot.
- **User & Execution Context**: Starts as `root`, drops privileges via `gosu` to UID `1000` / GID `1000`. Working directory `/palworld`.

---

## 3. Network Ports & Protocols

Declared ports under `spec.ports`:

| Port Name | Container Port | Protocol | Usage / Purpose |
|---|---|---|---|
| `game` | `8211` | `UDP` | Primary game traffic |
| `query` | `27015` | `UDP` | Steam server browser discovery |
| `rest-api` | `8212` | `TCP` | Palworld REST admin API |

---

## 4. Storage & Persistence Layout

- **Mount Path**: `/palworld`
- **Default Sizing**: `20Gi`
- **Persisted Content**:
  - SteamCMD install files (`/palworld/PalServer.sh`, binaries)
  - World saves (`/palworld/Pal/Saved/SaveGames`)
  - Server configuration files (`/palworld/Pal/Saved/Config/LinuxServer/PalWorldSettings.ini`)
  - Mod packages (`/palworld/Pal/Content/Paks`)
- **Non-Shadowing Invariant**: The mount path contains the SteamCMD game root and does not shadow container base utilities.

---

## 5. Administration & Remote Console (RCON)

- **Protocol**: `palworld` (REST admin API over HTTP Basic auth)
- **Console Mode**: `rcon`
- **Authentication**: HTTP Basic authentication (user `admin`), password supplied via `spec.rcon.passwordEnv: ADMIN_PASSWORD`.
- **Command Support**: REST endpoints for `announce`, `save`, `shutdown`, `stop`, `players`, `info`, and `metrics`.
- The `server-fps` readout parses `serverfps` from the metrics response as an integer frame rate in frames per second. Missing, null or malformed values yield no numeric sample.
- `samples/metrics.json` records the authenticated response of an empty Linux dedicated server, v1.0.5.102999 (Steam build 25247047). The instantaneous value was 59 FPS. The average FPS and frame time are separate engine fields.

---

## 6. Modding & Workshop Integration

- **Modding Framework**: Unreal Engine 5 `.pak` mods
- **Mod Directory Path**: `Pal/Content/Paks` (loader `pak`, extensions: `.pak`)
- **Workshop Synchronization**: Archive upload (.zip/.tar.gz/.pak) via Gameplane Mods tab.

---

## 7. Lifecycle & Graceful Shutdown

- **Stop Command Sequence (`spec.capabilities.lifecycle.stop`)**:
  ```yaml
  capabilities:
    lifecycle:
      stop:
        - "save"
        - "shutdown 1"
  ```
- **Signal Handling**: REST shutdown persists world state before terminating the process.

---

## 8. Key Invariants & Security

- **User Matching**: Image starts as root to perform chown before dropping privileges to UID `1000`. Therefore, `runAsUser` must remain unset in `spec.security`.
- **Filesystem Permissions**: `spec.security.fsGroup: 1000` ensures that the dropped-privilege user can write and execute files in `/palworld`.

---

## 9. References & Upstream Documentation

- Official Game Documentation: https://docs.palworldgame.com/
- Upstream Container Repository: https://github.com/thijsvanloef/palworld-server-docker
- Steam Dedicated Server AppID: `2394010`
