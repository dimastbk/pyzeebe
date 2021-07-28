from typing import Dict, List, Tuple

import grpc

from pyzeebe.grpc_internals.zeebe_adapter import ZeebeAdapter


class ZeebeClient(object):
    """A zeebe client that can connect to a zeebe instance and perform actions."""

    def __init__(
        self, grpc_channel: grpc.aio.Channel, max_connection_retries: int = 10
    ):
        """
        Args:
            grpc_channel (grpc.aio.Channel): GRPC Channel connected to a Zeebe gateway
            max_connection_retries (int): Amount of connection retries before client gives up on connecting to zeebe. To setup with infinite retries use -1
        """

        self.zeebe_adapter = ZeebeAdapter(grpc_channel, max_connection_retries)

    async def run_process(
        self, bpmn_process_id: str, variables: Dict = None, version: int = -1
    ) -> int:
        """
        Run process

        Args:
            bpmn_process_id (str): The unique process id of the process.
            variables (dict): A dictionary containing all the starting variables the process needs. Must be JSONable.
            version (int): The version of the process. Default: -1 (latest)

        Returns:
            int: process_instance_key, the unique id of the running process generated by Zeebe.

        Raises:
            ProcessDefinitionNotFoundError: No process with bpmn_process_id exists
            InvalidJSONError: variables is not JSONable
            ProcessDefinitionHasNoStartEventError: The specified process does not have a start event
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        return await self.zeebe_adapter.create_process_instance(
            bpmn_process_id=bpmn_process_id, variables=variables or {}, version=version
        )

    async def run_process_with_result(
        self,
        bpmn_process_id: str,
        variables: Dict = None,
        version: int = -1,
        timeout: int = 0,
        variables_to_fetch: List[str] = None,
    ) -> Tuple[int, Dict]:
        """
        Run process and wait for the result.

        Args:
            bpmn_process_id (str): The unique process id of the process.
            variables (dict): A dictionary containing all the starting variables the process needs. Must be JSONable.
            version (int): The version of the process. Default: -1 (latest)
            timeout (int): How long to wait until a timeout occurs. Default: 0 (Zeebe default timeout)
            variables_to_fetch (List[str]): Which variables to get from the finished process

        Returns:
            tuple: (The process instance key, A dictionary of the end state of the process instance)

        Raises:
            ProcessDefinitionNotFoundError: No process with bpmn_process_id exists
            InvalidJSONError: variables is not JSONable
            ProcessDefinitionHasNoStartEventError: The specified process does not have a start event
            ProcessTimeoutError: The process was not finished within the set timeout
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        return await self.zeebe_adapter.create_process_instance_with_result(
            bpmn_process_id=bpmn_process_id,
            variables=variables or {},
            version=version,
            timeout=timeout,
            variables_to_fetch=variables_to_fetch or [],
        )

    async def cancel_process_instance(self, process_instance_key: int) -> int:
        """
        Cancel a running process instance

        Args:
            process_instance_key (int): The key of the running process to cancel

        Returns:
            int: The process_instance_key

        Raises:
            ProcessInstanceNotFoundError: If no process instance with process_instance_key exists
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        await self.zeebe_adapter.cancel_process_instance(
            process_instance_key=process_instance_key
        )
        return process_instance_key

    async def deploy_process(self, *process_file_path: str) -> None:
        """
        Deploy one or more processes

        Args:
            process_file_path (str): The file path to a process definition file (bpmn/yaml)

        Raises:
            ProcessInvalidError: If one of the process file definitions is invalid
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        await self.zeebe_adapter.deploy_process(*process_file_path)

    async def publish_message(
        self,
        name: str,
        correlation_key: str,
        variables: Dict = None,
        time_to_live_in_milliseconds: int = 60000,
        message_id: str = None,
    ) -> None:
        """
        Publish a message

        Args:
            name (str): The message name
            correlation_key (str): The correlation key. For more info: https://docs.zeebe.io/glossary.html?highlight=correlation#correlation-key
            variables (dict): The variables the message should contain.
            time_to_live_in_milliseconds (int): How long this message should stay active. Default: 60000 ms (60 seconds)
            message_id (str): A unique message id. Useful for avoiding duplication. If a message with this id is still
                                active, a MessageAlreadyExists will be raised.

        Raises:
            MessageAlreadyExistError: If a message with message_id already exists
            ZeebeBackPressureError: If Zeebe is currently in back pressure (too many requests)
            ZeebeGatewayUnavailableError: If the Zeebe gateway is unavailable
            ZeebeInternalError: If Zeebe experiences an internal error

        """
        await self.zeebe_adapter.publish_message(
            name=name,
            correlation_key=correlation_key,
            time_to_live_in_milliseconds=time_to_live_in_milliseconds,
            variables=variables or {},
            message_id=message_id,
        )
