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
- Release packaging and GitHub Release publishing are automated.

## Implemented in v0.4.0

MessageFlow-compatible `/kcs2/` forwarding:

- `/kcs2/resources/ship/`
- `/kcs2/resources/map/`
- `/kcs2/resources/gauge/`
- `/kcs2/img/common/`
- `/kcs2/img/duty/`
- `/kcs2/img/sally/`
- binary image bodies transported as base64 over the bridge protocol and decoded by the plugin
- JSON bodies transported as UTF-8 text
- actual HTTP status and MIME type preserved
- plugin JAR manifest metadata added for logbook-kai plugin list display
- health output now includes API/image/JSON counters

## Tested environment

- Linux Mint 22.1 Xia / MATE / X11
- Google Chrome 153.0.8010.52
- logbook-kai 25.0.8
- Java 24.0.1

## Needs user-side verification

- v0.4.0 `/kcs2/` image/JSON capture and resource persistence
- plugin name/vendor/version/license display in logbook-kai
- Chrome unpacked extension persistence after OS/Chrome restart

## Not yet completed

- Multi-PC distribution / replay of current fleet state
- Connection failure desktop/browser notifications
- Policy-based Chrome extension deployment
- Long-term compatibility testing with future logbook-kai releases
