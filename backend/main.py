"""FastAPI backend for LLM Council."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import uuid
import json
import asyncio
import logging
import traceback

from . import storage
from .council import run_full_council, generate_conversation_title, stage1_collect_responses, stage2_collect_rankings, stage3_synthesize_final, calculate_aggregate_rankings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Council API")

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    pass


class SendMessageRequest(BaseModel):
    """Request to send a message in a conversation."""
    content: str


class ConversationMetadata(BaseModel):
    """Conversation metadata for list view."""
    id: str
    created_at: str
    title: str
    message_count: int


class Conversation(BaseModel):
    """Full conversation with all messages."""
    id: str
    created_at: str
    title: str
    messages: List[Dict[str, Any]]


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "LLM Council API"}


@app.get("/api/conversations", response_model=List[ConversationMetadata])
async def list_conversations():
    """List all conversations (metadata only)."""
    return storage.list_conversations()


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(conversation_id)
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Delete a specific conversation."""
    deleted = storage.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "deleted", "conversation_id": conversation_id}


@app.post("/api/conversations/{conversation_id}/message")
async def send_message(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    storage.add_user_message(conversation_id, request.content)

    # If this is the first message, generate a title
    if is_first_message:
        title = await generate_conversation_title(request.content)
        storage.update_conversation_title(conversation_id, title)

    # Run the 3-stage council process
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id,
        stage1_results,
        stage2_results,
        stage3_result
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(conversation_id: str, request: SendMessageRequest):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    logger.info(f"[STREAM START] conversation_id={conversation_id}, content_length={len(request.content)}")

    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id)
    if conversation is None:
        logger.error(f"[STREAM ERROR] Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0
    logger.info(f"[STREAM] is_first_message={is_first_message}")

    async def event_generator():
        try:
            logger.info("[STREAM] Adding user message")
            # Add user message
            storage.add_user_message(conversation_id, request.content)

            # Start title generation in parallel (don't await yet)
            title_task = None
            if is_first_message:
                logger.info("[STREAM] Starting title generation task")
                title_task = asyncio.create_task(generate_conversation_title(request.content))

            # Stage 1: Collect responses
            logger.info("[STREAM STAGE1] Starting stage 1")
            yield f"data: {json.dumps({'type': 'stage1_start'})}\n\n"

            try:
                stage1_results = await stage1_collect_responses(request.content)
                logger.info(f"[STREAM STAGE1] Completed - got {len(stage1_results)} responses")
                yield f"data: {json.dumps({'type': 'stage1_complete', 'data': stage1_results})}\n\n"
            except Exception as e:
                logger.error(f"[STREAM STAGE1 ERROR] {str(e)}\n{traceback.format_exc()}")
                raise

            # Stage 2: Collect rankings
            logger.info("[STREAM STAGE2] Starting stage 2")
            yield f"data: {json.dumps({'type': 'stage2_start'})}\n\n"

            try:
                stage2_results, label_to_model = await stage2_collect_rankings(request.content, stage1_results)
                aggregate_rankings = calculate_aggregate_rankings(stage2_results, label_to_model)
                logger.info(f"[STREAM STAGE2] Completed - got {len(stage2_results)} rankings")
                yield f"data: {json.dumps({'type': 'stage2_complete', 'data': stage2_results, 'metadata': {'label_to_model': label_to_model, 'aggregate_rankings': aggregate_rankings}})}\n\n"
            except Exception as e:
                logger.error(f"[STREAM STAGE2 ERROR] {str(e)}\n{traceback.format_exc()}")
                raise

            # Stage 3: Synthesize final answer
            logger.info("[STREAM STAGE3] Starting stage 3")
            yield f"data: {json.dumps({'type': 'stage3_start'})}\n\n"

            try:
                stage3_result = await stage3_synthesize_final(request.content, stage1_results, stage2_results)
                logger.info("[STREAM STAGE3] Completed")
                yield f"data: {json.dumps({'type': 'stage3_complete', 'data': stage3_result})}\n\n"
            except Exception as e:
                logger.error(f"[STREAM STAGE3 ERROR] {str(e)}\n{traceback.format_exc()}")
                raise

            # Wait for title generation if it was started
            if title_task:
                try:
                    logger.info("[STREAM] Waiting for title generation")
                    title = await title_task
                    storage.update_conversation_title(conversation_id, title)
                    logger.info(f"[STREAM] Title generated: {title}")
                    yield f"data: {json.dumps({'type': 'title_complete', 'data': {'title': title}})}\n\n"
                except Exception as e:
                    logger.error(f"[STREAM TITLE ERROR] {str(e)}\n{traceback.format_exc()}")
                    # Don't raise - title generation is optional

            # Save complete assistant message
            logger.info("[STREAM] Saving assistant message")
            storage.add_assistant_message(
                conversation_id,
                stage1_results,
                stage2_results,
                stage3_result
            )

            # Send completion event
            logger.info("[STREAM] Sending complete event")
            yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            logger.info("[STREAM END] Successfully completed")

        except Exception as e:
            # Send error event
            logger.error(f"[STREAM FATAL ERROR] {str(e)}\n{traceback.format_exc()}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
