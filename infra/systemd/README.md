# Linux Factory Worker (systemd)

A **bounded, reinstallable** alternative to GitHub-hosted Actions for the
existing `scripts/portfolio_audit.py`. This is an operational worker,
not a new product, not a paid service, and **not a coding agent**.
It runs without an AI subscription and never merges or publishes source code.

## Requirements
- A Linux VM, mini-PC, or VPS you control with systemd and Python 3.11+.
- An authorized way to obtain the PRIVATE repository on that machine.
- Network egress to `api.github.com` for fresh GitHub data, optionally.
- A least-privilege read-only fine-grained token scoped to exactly the private
  repos you want inspected. Without it, the snapshot is historical/unverified.

## One-time installation (on your own machine)

```bash
# Clone the existing private repo through your own authenticated SSH session.
# Do not insert PATs in Git URLs. Then place it at /opt/belentani-factory.
sudo useradd --system --home-dir /var/lib/belentani-factory \
  --shell /usr/sbin/nologin belentani-factory
sudo install -d -m 0700 -o belentani-factory -g belentani-factory \
  /var/lib/belentani-factory/artifacts/portfolio
sudo install -d -m 0700 /etc/belentani-factory

sudo install -m 0644 /opt/belentani-factory/infra/systemd/belentani-factory.service \
  /etc/systemd/system/belentani-factory.service
sudo install -m 0644 /opt/belentani-factory/infra/systemd/belentani-factory.timer \
  /etc/systemd/system/belentani-factory.timer

sudo install -m 0600 /opt/belentani-factory/infra/systemd/portfolio.env.example \
  /etc/belentani-factory/portfolio.env
# Privately edit the root-owned env file if you want LIVE private GitHub access.
sudoedit /etc/belentani-factory/portfolio.env

sudo systemd-analyze verify /etc/systemd/system/belentani-factory.service \
  /etc/systemd/system/belentani-factory.timer
sudo systemctl daemon-reload
sudo systemctl enable --now belentani-factory.timer
sudo systemctl start belentani-factory.service
```

Use a separate unprivileged account with read access to the checked-out
source and write access only to its designated `/var/lib` output directory.
The checkout should be owned by an administrator and not writable by the
worker. The example service grants no Linux capabilities and restricts writes
to `/var/lib/belentani-factory`.

## Check actual operation

```bash
systemctl list-timers belentani-factory.timer
systemctl status belentani-factory.service
journalctl -u belentani-factory.service --no-pager -n 100
sudo -u belentani-factory cat \
  /var/lib/belentani-factory/artifacts/portfolio/report.md
```

Each invocation first runs the repository's unit tests. A failing test aborts
the inventory. The Python script writes `inventory.json` and `report.md`
under `/var/lib/belentani-factory/artifacts/portfolio` with private permissions
(umask 0077). No upload, no implicit publish, no other repositories modified.

The timer schedules runs at 00:23, 04:23, 08:23, 12:23, 16:23 and 20:23
**in the host timezone**; systemd may coalesce to the 5-minute accuracy
window. Missed runs after reboot are handled by `Persistent=true`.
Stop or disable with `sudo systemctl disable --now belentani-factory.timer`.
To remove, delete the two unit files and reload systemd; retain the private
audit artifacts only as long as operationally needed.

## Explicit limits
- One systemd unit instance at a time (serialized by systemd).
- 12-minute timeout, 512 MiB memory limit, 50% single-CPU quota.
- 120 repository root checks maximum per live run, rotated automatically.
- No agent API invocation, automated coding, branch merges, deployments,
  permission modifications, GitHub secret writes or paid cloud allocation.
- This checkout's updates must be deployed separately by an authorized admin.
  The script does not auto-update itself or run remote shell content.

## Activation state

Files being committed to GitHub **do not install or enable this worker**.
It becomes active only after an authorized Linux device executes the steps
above. GitHub Actions and a ChatGPT scheduled task are separate systems.

## Next bounded step

When private GitHub access and a trusted Linux host are connected, a separate
worker can consume the inventory and open **reviewable, bounded** draft PRs
for an explicitly allowlisted project queue. That capability must be
implemented and tested before claiming automatic code completion.
