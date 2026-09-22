package local.kancolle.bridge;

import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;

import logbook.core.LogBookCoreServices;
import logbook.listener.ContentListenerSpi;
import logbook.net.RequestMetaData;
import logbook.net.ResponseMetaData;
import logbook.plugin.lifecycle.StartUp;

/**
 * PoC: receives already-captured Kancolle API traffic from the Chrome extension
 * on 127.0.0.1:8891 and feeds it into logbook-kai's existing ContentListenerSpi
 * pipeline. It does not make any request to the Kancolle servers.
 */
public final class KancolleBridgeStartUp implements StartUp {
    private static final int PORT = 8891;
    private static final int MAGIC = 0x4B435031; // "KCP1"
    private static final int VERSION = 1;
    private static final int MAX_PACKET = 32 * 1024 * 1024;

    private static final AtomicLong RECEIVED = new AtomicLong();
    private static final AtomicLong ACCEPTED = new AtomicLong();
    private static final AtomicLong ERRORS = new AtomicLong();

    private volatile boolean running = true;
    private ServerSocket server;

    @Override
    public void run() {
        ThreadPoolExecutor workers = new ThreadPoolExecutor(
            1, 4, 30L, TimeUnit.SECONDS,
            new ArrayBlockingQueue<>(64),
            r -> {
                Thread t = new Thread(r, "kancolle-cdp-bridge-worker");
                t.setDaemon(true);
                return t;
            },
            new ThreadPoolExecutor.CallerRunsPolicy()
        );

        try (ServerSocket ss = new ServerSocket()) {
            this.server = ss;
            ss.setReuseAddress(true);
            ss.bind(new InetSocketAddress(InetAddress.getLoopbackAddress(), PORT), 16);
            log("listening on 127.0.0.1:" + PORT);

            while (running && !Thread.currentThread().isInterrupted()) {
                Socket socket = ss.accept();
                workers.execute(() -> handleSocket(socket));
            }
        } catch (BindException e) {
            ERRORS.incrementAndGet();
            log("ERROR: port " + PORT + " is already in use: " + e);
        } catch (SocketException e) {
            if (running) {
                ERRORS.incrementAndGet();
                log("ERROR: socket: " + e);
            }
        } catch (Exception e) {
            ERRORS.incrementAndGet();
            log("ERROR: server: " + e);
        } finally {
            workers.shutdownNow();
        }
    }

    private void handleSocket(Socket socket) {
        try (socket) {
            socket.setSoTimeout(5000);
            BufferedInputStream in = new BufferedInputStream(socket.getInputStream());
            OutputStream out = socket.getOutputStream();

            String requestLine = readAsciiLine(in);
            if (requestLine == null || requestLine.isBlank()) return;

            String[] parts = requestLine.split(" ", 3);
            if (parts.length < 2) {
                sendText(out, 400, "Bad Request", "bad request");
                return;
            }

            String method = parts[0];
            String path = parts[1];

            int contentLength = 0;
            String line;
            while ((line = readAsciiLine(in)) != null && !line.isEmpty()) {
                int p = line.indexOf(':');
                if (p > 0) {
                    String name = line.substring(0, p).trim();
                    String value = line.substring(p + 1).trim();
                    if (name.equalsIgnoreCase("Content-Length")) {
                        try {
                            contentLength = Integer.parseInt(value);
                        } catch (NumberFormatException ignored) {}
                    }
                }
            }

            if ("OPTIONS".equals(method)) {
                sendText(out, 204, "No Content", "");
                return;
            }

            if ("GET".equals(method) && "/health".equals(path)) {
                String body = "OK received=" + RECEIVED.get()
                    + " accepted=" + ACCEPTED.get()
                    + " errors=" + ERRORS.get();
                sendText(out, 200, "OK", body);
                return;
            }

            if (!"POST".equals(method) || !"/ingest".equals(path)) {
                sendText(out, 404, "Not Found", "not found");
                return;
            }

            if (contentLength <= 0 || contentLength > MAX_PACKET) {
                ERRORS.incrementAndGet();
                sendText(out, 413, "Payload Too Large", "invalid length");
                return;
            }

            byte[] body = in.readNBytes(contentLength);
            if (body.length != contentLength) {
                ERRORS.incrementAndGet();
                sendText(out, 400, "Bad Request", "truncated");
                return;
            }

            RECEIVED.incrementAndGet();
            Packet packet = decode(body);
            dispatch(packet);
            ACCEPTED.incrementAndGet();

            sendText(out, 200, "OK", "ok");
        } catch (Exception e) {
            ERRORS.incrementAndGet();
            log("ERROR: ingest: " + e);
        }
    }

    private static Packet decode(byte[] bytes) throws IOException {
        try (DataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes))) {
            int magic = in.readInt();
            int version = in.readInt();
            long receivedAt = in.readLong();

            if (magic != MAGIC || version != VERSION) {
                throw new IOException("unsupported packet");
            }

            String method = readString(in);
            String uri = readString(in);
            String queryString = readString(in);
            String postData = readString(in);
            String responseBody = readString(in);

            if (!uri.startsWith("/kcsapi/")) {
                throw new IOException("unsupported URI: " + uri);
            }

            return new Packet(method, uri, queryString, postData, responseBody, receivedAt);
        }
    }

    private static void dispatch(Packet packet) {
        long requestAt = System.currentTimeMillis();
        RequestMetaData req = new Req(packet, requestAt);
        ResponseMetaData res = new Res(packet.responseBody(), System.currentTimeMillis());

        List<ContentListenerSpi> listeners =
            LogBookCoreServices.getServiceProviders(ContentListenerSpi.class).toList();

        int matched = 0;
        for (ContentListenerSpi listener : listeners) {
            try {
                if (listener.test(req)) {
                    matched++;
                    // Req/Res return a fresh InputStream on every call.
                    listener.accept(req, res);
                }
            } catch (Throwable t) {
                ERRORS.incrementAndGet();
                log("ERROR: listener " + listener.getClass().getName()
                    + " for " + packet.uri() + ": " + t);
            }
        }

        log("accepted " + packet.method() + " " + packet.uri()
            + " listeners=" + matched
            + " response=" + packet.responseBody().length());
    }

    private record Packet(
        String method,
        String uri,
        String queryString,
        String postData,
        String responseBody,
        long receivedAt
    ) {}

    private static final class Req implements RequestMetaData {
        private final Packet p;
        private final long requestAt;
        private final Map<String, List<String>> params;
        private final byte[] requestBody;

        Req(Packet p, long requestAt) {
            this.p = p;
            this.requestAt = requestAt;
            this.params = parseParams(p.queryString(), p.postData());
            this.requestBody = p.postData().getBytes(StandardCharsets.UTF_8);
        }

        @Override
        public String getContentType() {
            return "application/x-www-form-urlencoded";
        }

        @Override
        public String getMethod() {
            return p.method();
        }

        @Override
        public Map<String, List<String>> getParameterMap() {
            return params;
        }

        @Override
        public String getQueryString() {
            return p.queryString();
        }

        @Override
        public String getRequestURI() {
            return p.uri();
        }

        @Override
        public Optional<InputStream> getRequestBody() {
            return Optional.of(new ByteArrayInputStream(requestBody));
        }

        @Override
        public Optional<String> getHeader(String name) {
            if ("x-koukainissikai-receivedat".equalsIgnoreCase(name)) {
                return Optional.of(Long.toString(p.receivedAt()));
            }
            if ("x-koukainissikai-requestat".equalsIgnoreCase(name)) {
                return Optional.of(Long.toString(requestAt));
            }
            return Optional.empty();
        }
    }

    private static final class Res implements ResponseMetaData {
        private final byte[] body;
        private final long responseAt;

        Res(String body, long responseAt) {
            this.body = body.getBytes(StandardCharsets.UTF_8);
            this.responseAt = responseAt;
        }

        @Override
        public int getStatus() {
            return 200;
        }

        @Override
        public String getContentType() {
            return "text/plain; charset=UTF-8";
        }

        @Override
        public Optional<InputStream> getResponseBody() {
            return Optional.of(new ByteArrayInputStream(body));
        }

        @Override
        public Optional<String> getHeader(String name) {
            if ("x-koukainissikai-responseat".equalsIgnoreCase(name)) {
                return Optional.of(Long.toString(responseAt));
            }
            return Optional.empty();
        }
    }

    private static Map<String, List<String>> parseParams(String query, String post) {
        Map<String, List<String>> map = new LinkedHashMap<>();
        addEncodedParams(map, query);
        addEncodedParams(map, post);
        Map<String, List<String>> frozen = new LinkedHashMap<>();
        for (Map.Entry<String, List<String>> e : map.entrySet()) {
            frozen.put(e.getKey(), List.copyOf(e.getValue()));
        }
        return Collections.unmodifiableMap(frozen);
    }

    private static void addEncodedParams(Map<String, List<String>> map, String encoded) {
        if (encoded == null || encoded.isEmpty()) return;
        String s = encoded.startsWith("?") ? encoded.substring(1) : encoded;
        if (s.isEmpty()) return;

        for (String pair : s.split("&")) {
            if (pair.isEmpty()) continue;
            int eq = pair.indexOf('=');
            String rawKey = eq >= 0 ? pair.substring(0, eq) : pair;
            String rawVal = eq >= 0 ? pair.substring(eq + 1) : "";
            String key = urlDecode(rawKey);
            String val = urlDecode(rawVal);
            map.computeIfAbsent(key, k -> new ArrayList<>()).add(val);
        }
    }

    private static String urlDecode(String s) {
        try {
            return URLDecoder.decode(s, StandardCharsets.UTF_8);
        } catch (Exception e) {
            return s;
        }
    }

    private static String readString(DataInputStream in) throws IOException {
        int len = in.readInt();
        if (len < 0 || len > MAX_PACKET) {
            throw new IOException("invalid string length: " + len);
        }
        byte[] b = in.readNBytes(len);
        if (b.length != len) {
            throw new EOFException("truncated string");
        }
        return new String(b, StandardCharsets.UTF_8);
    }

    private static String readAsciiLine(InputStream in) throws IOException {
        ByteArrayOutputStream b = new ByteArrayOutputStream();
        int c;
        boolean gotAny = false;

        while ((c = in.read()) != -1) {
            gotAny = true;
            if (c == '\n') break;
            if (c != '\r') b.write(c);
            if (b.size() > 8192) throw new IOException("header line too long");
        }

        if (!gotAny && b.size() == 0) return null;
        return b.toString(StandardCharsets.ISO_8859_1);
    }

    private static void sendText(OutputStream out, int code, String reason, String body)
            throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        String headers =
            "HTTP/1.1 " + code + " " + reason + "\r\n"
            + "Content-Type: text/plain; charset=UTF-8\r\n"
            + "Content-Length: " + bytes.length + "\r\n"
            + "Access-Control-Allow-Origin: *\r\n"
            + "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
            + "Access-Control-Allow-Headers: Content-Type\r\n"
            + "Connection: close\r\n"
            + "\r\n";

        out.write(headers.getBytes(StandardCharsets.ISO_8859_1));
        out.write(bytes);
        out.flush();
    }

    private static void log(String s) {
        System.out.println("[KancolleCDPBridge] " + s);
    }
}
