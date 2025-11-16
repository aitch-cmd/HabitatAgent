from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from agents.alert.agent import AlertAgent
from a2a.utils import (
    new_task,
    new_agent_text_message
)

from a2a.utils.errors import ServerError

from a2a.types import (
    Task,
    TaskState,
    UnsupportedOperationError
)

import asyncio

class AlertAgentExecutor(AgentExecutor):
    """
    Alert Agent Executor - handles property alert creation and management.
    
    Let the agent call MCP tools directly for:
    - Creating alerts from natural language
    - Viewing user alerts
    - Deleting alerts
    - Searching matching properties
    """

    def __init__(self):
        self.agent = AlertAgent()
        self._initialized = False

    async def create(self):
        """Method to initialize the AlertAgentExecutor"""
        await self.agent.create()
        self._initialized = True

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """ 
        Let the agent handle alert management using MCP tools.
        
        The agent can:
        - Parse natural language to extract email, location, price
        - Create alerts in MongoDB
        - View user's existing alerts
        - Delete alerts
        - Search for matching properties
        """
        if not self._initialized:
            await self.create()

        query = context.get_user_input()

        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)

        task_id = task.id
        context_id = task.context_id

        updater = TaskUpdater(event_queue, task_id, context_id)

        try:
            async for item in self.agent.invoke(query, context_id):
                is_task_complete = item.get("is_task_complete", False)

                if not is_task_complete:
                    message = item.get('updates', 'Processing your alert request...')
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(message, context_id, task_id)
                    )
                else:
                    final_result = item.get('content', 'Alert operation completed')
                    await updater.update_status(
                        TaskState.completed,
                        new_agent_text_message(final_result, context_id, task_id)
                    )
                    await asyncio.sleep(0.1)
                    break
                    
        except Exception as e:
            error_msg = f"Alert operation failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"❌ {error_msg}\nPlease try again or check your input.",
                    context_id,
                    task_id
                )
            )
            raise
    
    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())