import dartio_tls

proxy = "http://customer-resi_4b78d26c-sessid-0211331481-sesstime-10:WYb%2B48cZoZ%2B1@pr.oxylabs.io:7777"

with dartio_tls.Client(impersonate="dartio_3_33_0", proxy=proxy, timeout=30) as c:
    r = c.get(
        "https://apis.ooredoo.dz/api/ooredoo-bff/subscriptions/getAccountInfo",
        headers=[
            ("x-msisdn", "2135XXXXXX"),
            ("user-agent", "Dart/3.11 (dart:io)"),
            ("authorization", "Bearer TOKEN"),
            ("x-device-fingerprint", "FP_FROM_REQABLE"),
            ("x-instance-id", "IID_FROM_REQABLE"),
            ("x-signature", "SIG_FROM_REQABLE"),
            ("x-platform-origin", "mobile-android"),
            ("platform", "android"),
            ("x-version", "1.5.17"),
            ("x-platform-data-signature", "PSIG_FROM_REQABLE"),
            ("x-timestamp", "TIMESTAMP"),
            ("x-correlation-id", "CORR"),
            ("accept", "*/*"),
        ]
    )
    print(r.status_code, r.text)
