"""
complete_task_tool.py
Tool for agent to complete task and provide final summary
"""

import json
import logging
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
def complete_task(
    total_leads_found: int,
    quality_leads_saved: int,
    summary_message: str
) -> str:
    """
    Complete the lead generation task and provide final summary.
    Call this when you have reached the target count OR completed max iterations.
    
    Args:
        total_leads_found: Total number of companies found/enriched
        quality_leads_saved: Number of quality leads saved (score >= 65, fit "high")
        summary_message: Brief summary of what was accomplished
    
    Returns: JSON string with completion status
    """
    logger.info(f"🏁 Task Complete - Saved {quality_leads_saved} quality leads out of {total_leads_found} found")
    logger.info(f"📝 Summary: {summary_message}")
    
    return json.dumps({
        "status": "complete",
        "total_found": total_leads_found,
        "quality_saved": quality_leads_saved,
        "message": summary_message,
        "task_completed": True
    })
