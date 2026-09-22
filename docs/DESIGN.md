# Design

## Components

### extension/

Independent Chrome Manifest V3 extension.

Responsibilities:

- attach only to the Kancolle DMM tab using `chrome.debugger`
- auto-attach to iframe/OOPIF targets
- enable CDP Network domain
- capture `/kcsapi/` request POST data and response bodies
- send only the required API data to localhost
- retain only metadata in Chrome storage for diagnostics

### plugin/

Companion plugin for logbook-kai.

Responsibilities:

- start a localhost-only listener on TCP/8891
- decode bridge packets
- adapt captured request/response data to logbook-kai metadata interfaces
- invoke logbook-kai's existing `ContentListenerSpi` pipeline

This module requires logbook-kai's plugin/API classes at build and runtime,
but does not bundle logbook-kai itself.

## Non-goals

- modifying Kancolle server traffic
- replacing logbook-kai's analysis/UI layer
- bundling or forking logbook-kai
- requiring logbook-kai-messageflow at runtime
