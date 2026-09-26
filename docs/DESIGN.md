# KLB Design

## Components

### KLB Chrome Extension (`extension/`)

Chrome Manifest V3 extension for KLB.

Responsibilities:

- attach only to the Kancolle DMM tab using `chrome.debugger`
- auto-attach to iframe/OOPIF targets
- enable CDP Network domain
- capture `/kcsapi/` request POST data and response bodies
- capture the same `/kcs2/` resource families used by logbook-kai-messageflow
- preserve response encoding, MIME type and status
- send captured data only to localhost
- retain only metadata in Chrome storage for diagnostics

The supported `/kcs2/` resource families are:

- `/kcs2/resources/ship/`
- `/kcs2/resources/map/`
- `/kcs2/resources/gauge/`
- `/kcs2/img/common/`
- `/kcs2/img/duty/`
- `/kcs2/img/sally/`

### bridge protocol

Protocol v2 extends the original PoC packet with:

- response encoding
- MIME type
- HTTP status

Binary CDP response bodies are transported as base64 text and decoded in the plugin.
The plugin retains protocol-v1 decoding for compatibility with the v0.3 extension during transition.

### KLB Logbook Plugin (`plugin/`)

Companion KLB plugin for logbook-kai.

Responsibilities:

- start a localhost-only listener on TCP/8891
- decode bridge packets
- restore binary image response bodies
- adapt captured request/response data to logbook-kai metadata interfaces
- invoke logbook-kai's existing `ContentListenerSpi` pipeline

This allows logbook-kai's own `APIListener` and `ImageListener` implementations
to continue handling API data, image persistence and sprite extraction.

This module requires logbook-kai's plugin/API classes at build and runtime,
but does not bundle logbook-kai itself.

## Non-goals

- modifying Kancolle server traffic
- replacing logbook-kai's analysis/UI layer
- reimplementing logbook-kai image storage or sprite extraction
- bundling or forking logbook-kai
- requiring logbook-kai-messageflow at runtime
