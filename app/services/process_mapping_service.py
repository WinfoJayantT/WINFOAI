# app/services/process_mapping_service.py
import logging
import json
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

import re

PREFIX_MBP_MAP = {
    "SUP": {"l1_process": "Supplier Invoice to Payment", "l2_process": "Manage Supplier Invoices", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "INV": {"l1_process": "Supplier Invoice to Payment", "l2_process": "Manage Supplier Invoices", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "PO": {"l1_process": "Requisition to Receipt", "l2_process": "Manage Purchase Orders", "product_mix": "ERP Cloud (Procurement)", "is_covered": True},
    "REQ": {"l1_process": "Requisition to Receipt", "l2_process": "Create Requisitions", "product_mix": "ERP Cloud (Procurement)", "is_covered": True},
    "AP": {"l1_process": "Supplier Invoice to Payment", "l2_process": "Execute Payments", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "PAY": {"l1_process": "Supplier Invoice to Payment", "l2_process": "Execute Payments", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "AR": {"l1_process": "Customer Invoice to Receipt", "l2_process": "Process Customer Invoices", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "REC": {"l1_process": "Customer Invoice to Receipt", "l2_process": "Process Customer Invoices", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "GL": {"l1_process": "Period Close To Financial Reports", "l2_process": "Close Ledgers", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "JRNL": {"l1_process": "Period Close To Financial Reports", "l2_process": "Record Journal Entries", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "FA": {"l1_process": "Asset to Retire", "l2_process": "Manage Asset Additions", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "EXP": {"l1_process": "Expense to Reimburse", "l2_process": "Submit Expense Reports", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "BANK": {"l1_process": "Bank Transaction to Cash Position", "l2_process": "Reconcile Bank Statements", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "CASH": {"l1_process": "Bank Transaction to Cash Position", "l2_process": "Manage Cash Positions", "product_mix": "ERP Cloud (Financials)", "is_covered": True},
    "P2P": {"l1_process": "Supplier Invoice to Payment", "l2_process": "Manage Supplier Invoices", "product_mix": "ERP Cloud (Financials, Procurement)", "is_covered": True},
    "O2C": {"l1_process": "Customer Invoice to Receipt", "l2_process": "Process Customer Invoices", "product_mix": "ERP Cloud (Financials, Order Management)", "is_covered": True},
}


class ProcessMappingService:
    def _load_mbp_mappings(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'oracle_mbp_mappings.json')
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load MBP mappings: {e}")
            return []

    def get_mapping_for_script(self, script: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Matches a PostgreSQL test script row to an Oracle Modern Best Practice (MBP) taxonomy mapping.
        Checks script prefix (INV, SUP, PO, etc.) and text matches across process/script names.
        """
        script_num = (script.get("test_script_number") or script.get("qualified_name") or "").upper()
        tokens = re.split(r'[\.\-\s\(\)_/]+', script_num)
        for token in tokens:
            if token in PREFIX_MBP_MAP:
                return PREFIX_MBP_MAP[token]

        script_name = (script.get("script_name") or "").lower()
        script_desc = (script.get("description") or "").lower()
        script_objective = (script.get("objective") or "").lower()
        script_process = (script.get("process") or "").lower()

        mappings = self._load_mbp_mappings()
        for item in mappings:
            l2 = item["l2_process"].lower()
            l1 = item["l1_process"].lower()
            if (
                (script_process and (script_process in l2 or script_process in l1)) or 
                (script_name and (l2 in script_name or l1 in script_name)) or
                (script_desc and l2 in script_desc) or
                (script_objective and l2 in script_objective)
            ):
                return item

        return None

process_mapping_service = ProcessMappingService()
