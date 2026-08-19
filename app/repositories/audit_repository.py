"""
Audit & Telemetry Repository
============================

This module provides data access for the `ai_tool_audit_logs` tracking table.
It serves as the historical ledger of all AI interactions, recording intent routing decisions,
tool payloads, performance metrics, and application errors.

Key Responsibilities:
  1. Immutable Logging: Appends a new audit record every time the Intent Router executes a tool.
  2. Telemetry Aggregation: Provides aggregated performance metrics (avg latency, success rate) 
     for the WinfoTest frontend analytics dashboard.
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from sqlalchemy import select, func, desc

from app.models.orm import AiToolAuditLog
from app.repositories.db import get_session

# ── logger initialization ───────────────────────────────────────────────
logger = logging.getLogger(__name__)


# ── class definition ──────────────────────────────────────────────────
class AuditRepository:
    """
    Data Access Object (DAO) for managing and querying AI Tool Audit Logs and system metrics.
    """

    # ── insertion operations ────────────────────────────────────────────
    def log_execution(
        self,
        tool_name: str,
        intent: Optional[str] = None,
        arguments_json: Optional[Dict[str, Any]] = None,
        status: str = "success",
        records_returned: int = 0,
        duration_ms: int = 0,
        error_message: Optional[str] = None,
        session_id: Optional[str] = "default",
        user_id: Optional[str] = "system",
        trace_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Creates a new immutable audit record in the database.
        
        Args:
            tool_name (str): The final tool selected by the LLM.
            intent (str, optional): The user's detected semantic intent.
            arguments_json (Dict, optional): The payload parsed from the LLM.
            status (str): "success" or "error".
            records_returned (int): Number of database records affected or retrieved.
            duration_ms (int): Total end-to-end execution latency.
            error_message (str, optional): Stack trace or handled error text if failed.
            
        Returns:
            Optional[str]: The UUID of the created audit log.
        """
        try:
            with get_session() as db:
                audit_entry = AiToolAuditLog(
                    audit_id=uuid4(),
                    session_id=session_id,
                    user_id=user_id,
                    intent=intent,
                    tool_name=tool_name,
                    arguments_json=arguments_json or {},
                    status=status,
                    records_returned=records_returned,
                    duration_ms=duration_ms,
                    error_message=error_message,
                    trace_id=trace_id,
                )
                db.add(audit_entry)
                db.commit()
                return str(audit_entry.audit_id)
        except Exception as exc:
            logger.warning(f"Failed to record AI tool audit log: {exc}")
            return None

    # ── telemetry retrieval ─────────────────────────────────────────────
    def get_recent_logs(self, limit: int = 25) -> List[Dict[str, Any]]:
        """
        Retrieves the most recent AI tool executions for frontend observability.
        """
        try:
            with get_session() as db:
                stmt = select(AiToolAuditLog).order_by(desc(AiToolAuditLog.timestamp)).limit(limit)
                rows = db.execute(stmt).scalars().all()
                
                return [
                    {
                        "audit_id": str(r.audit_id),
                        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                        "session_id": r.session_id,
                        "intent": r.intent,
                        "tool_name": r.tool_name,
                        "arguments": r.arguments_json,
                        "status": r.status,
                        "records_returned": r.records_returned,
                        "duration_ms": r.duration_ms,
                        "error_message": r.error_message,
                    }
                    for r in rows
                ]
        except Exception as exc:
            logger.error(f"Failed to fetch recent audit logs: {exc}")
            return []

    def get_telemetry_summary(self) -> Dict[str, Any]:
        """
        Calculates aggregate statistics across all AI tool executions.
        
        Returns:
            Dict: Payload containing total calls, avg latency, error counts, and tool distribution.
        """
        try:
            with get_session() as db:
                total_calls = db.execute(select(func.count(AiToolAuditLog.audit_id))).scalar() or 0
                avg_duration = db.execute(select(func.avg(AiToolAuditLog.duration_ms))).scalar() or 0.0
                error_count = db.execute(
                    select(func.count(AiToolAuditLog.audit_id)).where(AiToolAuditLog.status != "success")
                ).scalar() or 0

                # Calculate distribution of which AI tools are used most frequently
                tool_stmt = (
                    select(AiToolAuditLog.tool_name, func.count(AiToolAuditLog.audit_id))
                    .group_by(AiToolAuditLog.tool_name)
                    .order_by(desc(func.count(AiToolAuditLog.audit_id)))
                )
                tool_counts = {t: c for t, c in db.execute(tool_stmt).all()}

                return {
                    "total_calls": int(total_calls),
                    "avg_duration_ms": round(float(avg_duration), 1),
                    "error_count": int(error_count),
                    "success_rate": round(100.0 * (total_calls - error_count) / max(total_calls, 1), 1),
                    "tool_distribution": tool_counts,
                }
        except Exception as exc:
            logger.error(f"Failed to calculate telemetry summary: {exc}")
            return {
                "total_calls": 0,
                "avg_duration_ms": 0.0,
                "error_count": 0,
                "success_rate": 100.0,
                "tool_distribution": {},
            }


# ── singleton export ──────────────────────────────────────────────────
audit_repository = AuditRepository()
