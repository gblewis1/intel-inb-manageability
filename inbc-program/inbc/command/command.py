"""
    Command classes to represent command entered by user.

    # Copyright (C) 2020-2023 Intel Corporation
    # SPDX-License-Identifier: Apache-2.0
"""

import logging
import time
from typing import Any, Optional
from abc import ABC, abstractmethod

from ..constants import COMMAND_SUCCESS, COMMAND_FAIL
from ..ibroker import IBroker
from ..inbc_exception import InbcCode
from ..utility import search_keyword

from inbm_lib.timer import Timer
from inbm_common_lib.request_message_constants import DYNAMIC_TELEMETRY, \
    OTA_IN_PROGRESS    
from inbm_common_lib.request_message_constants import DBS_LOG, DOCKER_NAME, DOCKER_MESSAGE

logger = logging.getLogger(__name__)


class Command(ABC):
    """Base class for command objects

    @param timer_limit: max time for timer to wait for command completion
    @param broker: Broker object
    @param cmd_type: name of command to execute
    """

    def __init__(self, timer_limit: int, broker: IBroker, cmd_type: str) -> None:
        self._update_timer = Timer(timer_limit, self._timer_expired, is_daemon=True)
        self._broker = broker
        self._cmd_type = cmd_type

    def stop_timer(self):
        """Stops the timer which is waiting for the command to execute."""
        self._update_timer.stop()

    @abstractmethod
    def trigger_manifest(self, args: Any, topic: str) -> None:
        """Trigger the command-line utility tool to invoke update.

        @param args: arguments passed to command-line tool.
        @param topic: MQTT topic to publish the manifest.
        """
        manifest = args.func(args)
        self._broker.publish(topic, manifest)
        self._update_timer.start()

    @abstractmethod
    def search_response(self, payload: str) -> None:
        """Search for keywords in response message

        @param payload: payload received in which to search
        """
        if self._cmd_type != "query":
            if search_keyword(payload, ["SUCCESSFUL"]):
                self.terminate_operation(COMMAND_SUCCESS, InbcCode.SUCCESS.value)
            else:
                self.terminate_operation(COMMAND_FAIL, InbcCode.FAIL.value)

    @abstractmethod
    def search_event(self, payload: str, topic: str) -> None:
        """Search for keywords in event message

        @param payload: payload received in which to search
        @param topic: topic from which message was received
        """
        if not search_keyword(payload, [DYNAMIC_TELEMETRY, DBS_LOG, DOCKER_NAME, DOCKER_MESSAGE]):
            logger.info('Message received: %s on topic: %s', payload, topic)

        if search_keyword(payload, ["/usr/bin/mender -install"]):
            print("\n Flashing mender file. This will take several minutes...")

    def _search_for_busy(self, payload: str) -> None:
        if search_keyword(payload, [OTA_IN_PROGRESS]):
            self.terminate_operation(COMMAND_FAIL, InbcCode.HOST_BUSY.value)

    def _timer_expired(self) -> None:
        """Callback method when timer has expired"""
        logger.debug('\n Timer expired. INBC terminating')
        self.terminate_operation(COMMAND_FAIL, InbcCode.COMMAND_TIMED_OUT.value)

    def terminate_operation(self, status: str, return_code: int) -> None:
        """Stop INBC after getting expected response

        @param status: success or failure response
        @param return_code: INBC return code
        """
        if status == COMMAND_SUCCESS:
            print(f"\n {self._cmd_type.upper()} Command Execution is Completed")
        elif status == COMMAND_FAIL:
            print(f"\n {self._cmd_type.upper()} Command Execution FAILED")
            shared.exit_code = abs(return_code)
        logger.info("INBC code: {0}".format(return_code))
        shared.running = False
        self._update_timer.stop()

