from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater

from agents.search.agent import SearchAgent
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


class SearchAgentExecutor(AgentExecutor):
    """
    Simplified executor - let the agent call MCP tools directly.
    """

    def __init__(self):
        self.agent = SearchAgent()
        self._initialized = False

    async def create(self):
        """
        Factory method to initialize the SearchAgentExecutor.
        """
        await self.agent.create()
        self._initialized = True

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Let the agent handle the entire search workflow using its MCP tools.
        """
        
        if not self._initialized:
            await self.create()
        
        # Extract the user's search query
        query = context.get_user_input()
        
        # Get or create task
        task = context.current_task
        if not task:
            task = new_task(context.message)
            await event_queue.enqueue_event(task)
        
        task_id = task.id
        context_id = task.context_id
        
        # Create updater
        updater = TaskUpdater(event_queue, task_id, context_id)
        
        try:
            # Let the agent do everything - it has the MCP tools
            async for item in self.agent.invoke(query, context_id):
                is_task_complete = item.get("is_task_complete", False)

                if not is_task_complete:
                    message = item.get('updates', 'Searching for properties...')
                    await updater.update_status(
                        TaskState.working,
                        new_agent_text_message(message, context_id, task_id)
                    )
                else:
                    final_result = item.get('content', 'No results found')
                    await updater.update_status(
                        TaskState.completed,
                        new_agent_text_message(final_result, context_id, task_id)
                    )
                    await asyncio.sleep(0.1)
                    break
                    
        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            print(f"❌ {error_msg}")
            
            await updater.update_status(
                TaskState.failed,
                new_agent_text_message(
                    f"❌ {error_msg}\nPlease try again.",
                    context_id,
                    task_id
                )
            )
            raise

    async def cancel(self, request: RequestContext, event_queue: EventQueue) -> Task | None:
        raise ServerError(error=UnsupportedOperationError())