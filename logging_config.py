# Import `logger` from this module in other modules to use the shared configuration.
import logging


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="[ %(levelname)s ] %(asctime)s %(name)s: %(message)s",
    )


configure_logging()

# Export a module-level logger for the application to use
logger = logging.getLogger("playradarhub")
