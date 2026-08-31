import ssl


def ssl_context(verify_ssl: bool) -> ssl.SSLContext:
    # Anki's bundled OpenSSL often fails CA checks (e.g. Missing Authority Key
    # Identifier) even when the same URL works in Postman/browsers.
    if not verify_ssl:
        return ssl._create_unverified_context()
    return ssl.create_default_context()
