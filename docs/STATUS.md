# Current status

## Verified

- Main Chrome profile can be used.
- DevTools UI / logbook-kai DevTools panel is not required.
- Kancolle OOPIF/iframe `/kcsapi/` traffic can be captured through CDP.
- POST body and response body can be captured.
- Data can be delivered directly to a logbook-kai plugin on `127.0.0.1:8891`.
- logbook-kai updates while `logbook-kai-messageflow.jar` is stopped.
- The direct bridge listener is bound to localhost only.
- Chrome debugger warning can be suppressed when Chrome is started with
  `--silent-debugger-extension-api`.

## Tested environment

- Linux Mint 22.1 Xia / MATE / X11
- Google Chrome 153.0.8010.52
- logbook-kai 25.0.8
- Java 24.0.1

## Not yet completed

- Multi-PC distribution / replay of current fleet state
- `/kcs2/` image / JSON handling in the direct path
- Packaging / release automation
- Policy-based Chrome extension deployment
- Long-term compatibility testing with future logbook-kai releases
