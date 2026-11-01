import os
import sentry_sdk
def init_sentry() -> bool:
   
    dsn = os.getenv("SENTRY_DSN")
    if not dsn:
        print("ℹ️  SENTRY_DSN not set: running without tracing.")
        return False

    sentry_sdk.init(
        dsn=dsn, 
        traces_sample_rate=1.0,
        send_default_pii=True,
        environment="local", 
    )
    return True