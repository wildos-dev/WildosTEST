"""start up and run wildosnode"""

import logging
import os
import sys

from grpclib.health.service import Health
from grpclib.server import Server
from grpclib.utils import graceful_exit

from wildosnode.backends.hysteria2.hysteria2_backend import HysteriaBackend
from wildosnode.backends.singbox.singbox_backend import SingBoxBackend
from wildosnode.backends.xray.xray_backend import XrayBackend
from wildosnode.config import (
    HYSTERIA_EXECUTABLE_PATH,
    HYSTERIA_CONFIG_PATH,
    XRAY_CONFIG_PATH,
    HYSTERIA_ENABLED,
    XRAY_ENABLED,
    XRAY_EXECUTABLE_PATH,
    XRAY_ASSETS_PATH,
    SING_BOX_ENABLED,
    SING_BOX_EXECUTABLE_PATH,
    SING_BOX_CONFIG_PATH,
    SERVICE_ADDRESS,
    SERVICE_PORT,
    INSECURE,
    SSL_CERT_FILE,
    SSL_KEY_FILE,
    SSL_CLIENT_CERT_FILE,
)
from wildosnode.service import WildosService
from wildosnode.storage import MemoryStorage
from wildosnode.utils.ssl import generate_keypair, create_secure_context

logger = logging.getLogger(__name__)


async def main():
    """start up and run xray and the service"""
    if INSECURE:
        ssl_context = None
        logger.info("Running in insecure mode without SSL certificates.")
    else:
        if not all(
            (os.path.isfile(SSL_CERT_FILE), os.path.isfile(SSL_KEY_FILE))
        ):
            logger.info("Generating a keypair for WildosNode.")
            try:
                generate_keypair(SSL_KEY_FILE, SSL_CERT_FILE)
            except Exception as e:
                logger.error("Failed to generate SSL keypair: %s", e)
                logger.info("Switching to insecure mode.")
                ssl_context = None
            else:
                ssl_context = create_secure_context(
                    SSL_CERT_FILE,
                    SSL_KEY_FILE,
                    trusted=SSL_CLIENT_CERT_FILE if os.path.isfile(SSL_CLIENT_CERT_FILE) else None,
                )
        else:
            if not SSL_CLIENT_CERT_FILE or not os.path.isfile(SSL_CLIENT_CERT_FILE):
                logger.warning("No client certificate found, using only server certificate.")
                ssl_context = create_secure_context(
                    SSL_CERT_FILE,
                    SSL_KEY_FILE,
                    trusted=None,
                )
            else:
                ssl_context = create_secure_context(
                    SSL_CERT_FILE,
                    SSL_KEY_FILE,
                    trusted=SSL_CLIENT_CERT_FILE,
                )

    storage = MemoryStorage()
    backends = dict()
    
    if XRAY_ENABLED:
        try:
            if not os.path.isfile(XRAY_EXECUTABLE_PATH):
                logger.error("Xray executable not found at %s", XRAY_EXECUTABLE_PATH)
            else:
                xray_backend = XrayBackend(
                    XRAY_EXECUTABLE_PATH,
                    XRAY_ASSETS_PATH,
                    XRAY_CONFIG_PATH,
                    storage,
                )
                await xray_backend.start()
                backends.update({"xray": xray_backend})
                logger.info("Xray backend started successfully")
        except Exception as e:
            logger.error("Failed to start Xray backend: %s", e)
    
    if HYSTERIA_ENABLED:
        try:
            if not os.path.isfile(HYSTERIA_EXECUTABLE_PATH):
                logger.error("Hysteria executable not found at %s", HYSTERIA_EXECUTABLE_PATH)
            else:
                hysteria_backend = HysteriaBackend(
                    HYSTERIA_EXECUTABLE_PATH, HYSTERIA_CONFIG_PATH, storage
                )
                await hysteria_backend.start()
                backends.update({"hysteria2": hysteria_backend})
                logger.info("Hysteria backend started successfully")
        except Exception as e:
            logger.error("Failed to start Hysteria backend: %s", e)
    
    if SING_BOX_ENABLED:
        try:
            if not os.path.isfile(SING_BOX_EXECUTABLE_PATH):
                logger.error("Sing-box executable not found at %s", SING_BOX_EXECUTABLE_PATH)
            else:
                sing_box_backend = SingBoxBackend(
                    SING_BOX_EXECUTABLE_PATH, SING_BOX_CONFIG_PATH, storage
                )
                await sing_box_backend.start()
                backends.update({"sing-box": sing_box_backend})
                logger.info("Sing-box backend started successfully")
        except Exception as e:
            logger.error("Failed to start Sing-box backend: %s", e)

    if not backends:
        logger.warning("No backends enabled or successfully started. Service will run with no backends.")
    
    server = Server([WildosService(storage, backends), Health()])

    with graceful_exit([server]):
        await server.start(SERVICE_ADDRESS, SERVICE_PORT, ssl=ssl_context)
        logger.info(
            "Node service running on %s:%i (SSL: %s)", 
            SERVICE_ADDRESS, 
            SERVICE_PORT,
            "enabled" if ssl_context else "disabled"
        )
        await server.wait_closed()
