import uvicorn
from nexus.core.main import app
from nexus.shared.config import CoreConfig

config = CoreConfig()
uvicorn_kwargs = {
    "host": config.host,
    "port": config.port,
    "reload": config.env == "development",
    "log_level": config.log_level.lower(),
}
if config.ssl_keyfile and config.ssl_certfile:
    uvicorn_kwargs["ssl_keyfile"] = str(config.ssl_keyfile)
    uvicorn_kwargs["ssl_certfile"] = str(config.ssl_certfile)

if __name__ == "__main__":
    uvicorn.run("nexus.core.main:app", **uvicorn_kwargs)
