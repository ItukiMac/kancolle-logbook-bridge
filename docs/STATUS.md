# Current status

## Verified

- Main Chrome profile can be used.
- DevTools UI / logbook-kai DevTools panel is not required.
- Kancolle OOPIF/iframe `/kcsapi/` traffic can be captured through CDP.
- POST body and response body can be captured.
- Data can be delivered directly to a logbook-kai plugin on `127.0.0.1:8891`.
- logbook-kai updates while `logbook-kai-messageflow.jar` is stopped.
- The direct bridge listener is bound to localhost only.
- Chrome debugger warning can be suppressed with `--silent-debugger-extension-api`.
- Release packaging and GitHub Release publishing are automated.
- MessageFlow-compatible `/kcs2/` image/JSON forwarding is verified in actual use.
  - observed: `received=54 accepted=54 api=7 image=34 json=13 errors=0`
- Plugin metadata is visible in logbook-kai:
  - Kancolle CDP Bridge / ItukiMac / version / MIT
- The unpacked Chrome extension remains registered after reboot from its fixed path.

## Implemented in v0.5.x / v0.6.0

Connection-loss monitoring and notification:

- Chrome extension sends a heartbeat every 30 seconds while a monitored Kancolle tab is active.
- v0.5.1 fixes watchdog arming: actual CDP attachment and successful ingest traffic both establish `connected` state.
- v0.5.2 persists Chrome-side failure/alert state in `chrome.storage.local` so MV3 service-worker suspension does not reset the 3-failure notification threshold.
- Chrome notifies immediately when `/ingest` fails.
- Chrome notifies after 3 consecutive heartbeat failures (about 90 seconds).
- Chrome sends a one-shot recovery notification after connectivity returns.
- Chrome sends `active=false` when monitoring is intentionally stopped or no monitored game tab remains.
- Plugin exposes `POST /heartbeat`.
- Plugin watchdog changes state through `waiting -> connected -> lost`.
- Plugin uses Linux Mint `notify-send` for one-shot loss/recovery notifications.
- Plugin reports `chrome=<state>` and `heartbeatAge=<seconds>` in `/health`.
- Plugin uses `System.nanoTime()` for heartbeat age so normal system suspend does not count toward the timeout.
- Bind failure on TCP/8891 triggers a desktop notification.

## v0.6.0 changes

- Connection-loss detection target reduced from about 90 seconds to about 30 seconds.
- Chrome side alerts on the first failed 30-second heartbeat check.
- Plugin watchdog timeout reduced to 30 seconds and checks every 5 seconds.
- Plugin adds a compact Direct Bridge status strip to the logbook-kai main window.
- Status strip shows state, heartbeat age, API/image/JSON counters, and error count.
- `/health` now includes `timeout=30`.
- Chrome popup and `/health` remain available as non-notification fallback status views.

## Existing MessageFlow-compatible resource forwarding

- `/kcs2/resources/ship/`
- `/kcs2/resources/map/`
- `/kcs2/resources/gauge/`
- `/kcs2/img/common/`
- `/kcs2/img/duty/`
- `/kcs2/img/sally/`
- binary image bodies transported as base64 and decoded by the plugin
- JSON bodies transported as UTF-8 text
- HTTP status and MIME type preserved

## Tested environment

- Linux Mint 22.1 Xia / MATE / X11
- Google Chrome 153.0.8010.52
- logbook-kai 25.0.8
- Java 24.0.1

## Needs user-side verification

- v0.5.0 Chrome notification on plugin outage
- v0.5.0 plugin desktop notification on Chrome/extension outage
- recovery notifications on both sides
- no notification after intentional monitoring stop / closing the Kancolle tab

## Not yet completed

- Multi-PC distribution / replay of current fleet state
- Policy-based Chrome extension deployment
- Long-term compatibility testing with future logbook-kai releases
