from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from .client import FileMakerClient
from .exceptions import (
    FileMakerAmbiguousResultError,
    FileMakerDuplicateError,
    FileMakerNotFoundError,
    FileMakerValidationError,
)
from .layouts import CAANFields, ContractFields, Layouts, ProjectFields, RFIFields


class BusinessServicesFileMakerClient:
    """
    Higher-level business client for the UCSC Business Services FileMaker app.

    Public lookup methods are intentionally exposed because they are useful as
    standalone SDK operations in scripts, spreadsheets, and notebooks.
    Higher-level methods return normalized snake_case keys while preserving the
    original FileMaker record under `raw_fields`.
    """

    SPEC_SECTION_NUMBER_RE = re.compile(r"(\d{6})")

    def __init__(self, client: FileMakerClient) -> None:
        """Wrap a low-level FileMaker client with business helpers."""
        self.client = client

    def find_projects(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        project_number: str | None = None,
        project_name: str | None = None,
        id_primary: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Find project records and return normalized project dictionaries."""
        merged_criteria = self._merge_criteria(
            criteria,
            {
                ProjectFields.ID_PRIMARY: id_primary,
                ProjectFields.PROJECT_NUMBER: project_number,
                ProjectFields.PROJECT_NAME: project_name,
            },
        )
        records = self.client.find_matching(
            merged_criteria,
            layout_name=Layouts.PROJECTS,
            limit=limit,
        )
        return [self._normalize_project_record(record) for record in records]

    def get_project(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        project_number: str | None = None,
        project_name: str | None = None,
        id_primary: str | None = None,
    ) -> dict[str, Any]:
        """Return exactly one matching project or raise a typed error."""
        records = self.find_projects(
            criteria=criteria,
            project_number=project_number,
            project_name=project_name,
            id_primary=id_primary,
            limit=10,
        )
        return self._require_single_result(records, "project")

    def find_contracts(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        project_id_primary: str | None = None,
        project_number: str | None = None,
        contract_number: str | None = None,
        raw_contract_number: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Find contract records and return normalized contract dictionaries."""
        merged_criteria = self._merge_criteria(
            criteria,
            {
                ContractFields.PROJECT_ID: project_id_primary,
                ContractFields.EFFECTIVE_CONTRACT_NUMBER: contract_number or project_number,
                ContractFields.LEGACY_CONTRACT_NUMBER: raw_contract_number,
            },
        )
        records = self.client.find_matching(
            merged_criteria,
            layout_name=Layouts.CONTRACTS,
            limit=limit,
        )
        return [self._normalize_contract_record(record) for record in records]

    def get_contract(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        project_id_primary: str | None = None,
        project_number: str | None = None,
        contract_number: str | None = None,
        raw_contract_number: str | None = None,
    ) -> dict[str, Any]:
        """Return exactly one matching contract or raise a typed error."""
        records = self.find_contracts(
            criteria=criteria,
            project_id_primary=project_id_primary,
            project_number=project_number,
            contract_number=contract_number,
            raw_contract_number=raw_contract_number,
            limit=10,
        )
        return self._require_single_result(records, "contract")

    def get_contract_for_project(
        self,
        *,
        project: Mapping[str, Any] | None = None,
        project_criteria: Mapping[str, Any] | None = None,
        contract_criteria: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve the single contract associated with a project."""
        resolved_project = dict(project) if project is not None else self.get_project(criteria=project_criteria)
        project_id_primary = resolved_project.get("id_primary") or resolved_project.get(ProjectFields.ID_PRIMARY)
        if not project_id_primary:
            raise FileMakerValidationError(
                "Resolved project is missing required field 'id_primary'."
            )

        records = self.find_contracts(
            criteria=contract_criteria,
            project_id_primary=str(project_id_primary),
            limit=10,
        )
        return self._require_single_result(records, "contract")

    def resolve_project_contract_context(
        self,
        *,
        project: Mapping[str, Any] | None = None,
        project_criteria: Mapping[str, Any] | None = None,
        contract_criteria: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve exactly one project and exactly one associated contract."""
        resolved_project = dict(project) if project is not None else self.get_project(criteria=project_criteria)
        resolved_contract = self.get_contract_for_project(
            project=resolved_project,
            contract_criteria=contract_criteria,
        )
        contract_id_primary = resolved_contract.get("id_primary") or resolved_contract.get(ContractFields.ID_PRIMARY)
        if not contract_id_primary:
            raise FileMakerValidationError(
                "Resolved contract is missing required field id_primary."
            )

        return {
            "project": resolved_project,
            "contract": resolved_contract,
            "contract_id_primary": contract_id_primary,
        }

    def find_rfis(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        contract_id_primary: str | None = None,
        rfi_number: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Find RFI records and return normalized RFI dictionaries."""
        merged_criteria = self._merge_criteria(
            criteria,
            {
                RFIFields.CONTRACT_ID: contract_id_primary,
                RFIFields.RFI_NUMBER: rfi_number,
            },
        )
        records = self.client.find_matching(
            merged_criteria,
            layout_name=Layouts.RFIS,
            limit=limit,
        )
        return [self._normalize_rfi_record(record) for record in records]

    def get_rfi(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        contract_id_primary: str | None = None,
        rfi_number: str | None = None,
    ) -> dict[str, Any]:
        """Return exactly one matching RFI or raise a typed error."""
        records = self.find_rfis(
            criteria=criteria,
            contract_id_primary=contract_id_primary,
            rfi_number=rfi_number,
            limit=10,
        )
        return self._require_single_result(records, "RFI")

    def recent_rfis_for_contract(
        self,
        *,
        contract_id_primary: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return recent RFIs for a contract, sorted by RFI number descending."""
        records = self.client.find(
            [{RFIFields.CONTRACT_ID: "==" + str(contract_id_primary)}],
            layout_name=Layouts.RFIS,
            limit=limit,
            sort=[{"fieldName": RFIFields.RFI_NUMBER, "sortOrder": "descend"}],
        )
        return [self._normalize_rfi_record(record) for record in records]

    def find_caans(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        caan: str | None = None,
        name: str | None = None,
        description: str | None = None,
        id_primary: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Find CAAN records by exact field criteria."""
        merged_criteria = self._merge_criteria(
            criteria,
            {
                CAANFields.ID_PRIMARY: id_primary,
                CAANFields.CAAN: caan,
                CAANFields.NAME: name,
                CAANFields.DESCRIPTION: description,
            },
        )
        records = self.client.find_matching(
            merged_criteria,
            layout_name=Layouts.CAANS,
            limit=limit,
        )
        return [self._normalize_caan_record(record) for record in records]

    def get_caan(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        caan: str | None = None,
        name: str | None = None,
        description: str | None = None,
        id_primary: str | None = None,
    ) -> dict[str, Any]:
        """Return exactly one matching CAAN or raise a typed error."""
        records = self.find_caans(
            criteria=criteria,
            caan=caan,
            name=name,
            description=description,
            id_primary=id_primary,
            limit=10,
        )
        return self._require_single_result(records, "CAAN")

    def search_caans(
        self,
        search_text: str,
        *,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search CAAN names and descriptions for a text fragment."""
        search_text = search_text.strip()
        if not search_text:
            raise FileMakerValidationError("CAAN search text is required.")

        records = self.client.find(
            [
                {CAANFields.NAME: f"*{search_text}*"},
                {CAANFields.DESCRIPTION: f"*{search_text}*"},
            ],
            layout_name=Layouts.CAANS,
            limit=limit,
        )
        return [self._normalize_caan_record(record) for record in records]

    def create_rfi(
        self,
        rfi_data: Mapping[str, Any],
        *,
        allow_duplicate: bool = False,
    ) -> Any:
        """Create an RFI after validating required fields and duplicates."""
        payload = self._build_rfi_payload(rfi_data)
        contract_id_primary = payload[RFIFields.CONTRACT_ID]
        rfi_number = payload[RFIFields.RFI_NUMBER]

        if not allow_duplicate:
            existing = self.find_rfis(
                contract_id_primary=str(contract_id_primary),
                rfi_number=str(rfi_number),
                limit=5,
            )
            if existing:
                raise FileMakerDuplicateError(
                    f"An RFI already exists for contract {contract_id_primary!r} with number {rfi_number!r}."
                )

        return self.client.create_record(payload, layout_name=Layouts.RFIS)

    def preview_rfi_for_project(
        self,
        *,
        project_criteria: Mapping[str, Any],
        rfi_data: Mapping[str, Any],
        contract_criteria: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve RFI context and return the payload and duplicate matches."""
        context = self.resolve_project_contract_context(
            project_criteria=project_criteria,
            contract_criteria=contract_criteria,
        )
        payload = self._build_rfi_payload(
            rfi_data,
            contract_id_primary=context["contract_id_primary"],
        )
        duplicates: list[dict[str, Any]] = []
        for candidate in self._rfi_number_duplicate_candidates(str(payload[RFIFields.RFI_NUMBER])):
            duplicates.extend(
                self.find_rfis(
                    contract_id_primary=str(context["contract_id_primary"]),
                    rfi_number=candidate,
                    limit=5,
                )
            )

        return {
            "project": context["project"],
            "contract": context["contract"],
            "duplicates": self._dedupe_records(duplicates),
            "payload": payload,
        }

    def create_rfi_for_project(
        self,
        *,
        project_criteria: Mapping[str, Any],
        rfi_data: Mapping[str, Any],
        contract_criteria: Mapping[str, Any] | None = None,
    ) -> Any:
        """Resolve project and contract context, then create an RFI."""
        preview = self.preview_rfi_for_project(
            project_criteria=project_criteria,
            rfi_data=rfi_data,
            contract_criteria=contract_criteria,
        )
        if preview["duplicates"]:
            contract_id_primary = preview["payload"][RFIFields.CONTRACT_ID]
            rfi_number = preview["payload"][RFIFields.RFI_NUMBER]
            raise FileMakerDuplicateError(
                f"An RFI already exists for contract {contract_id_primary!r} with number {rfi_number!r}."
            )
        return self.client.create_record(preview["payload"], layout_name=Layouts.RFIS)

    @classmethod
    def extract_spec_section(cls, submittal_item_number: str) -> str:
        """Extract a six-digit spec section and format it as paired digits."""
        match = cls.SPEC_SECTION_NUMBER_RE.search(submittal_item_number or "")
        if not match:
            raise FileMakerValidationError(
                "Submittal item number must contain a six-digit spec section."
            )

        digits = match.group(1)
        return f"{digits[:2]} {digits[2:4]} {digits[4:6]}"

    @staticmethod
    def _normalize_project_record(record: Mapping[str, Any]) -> dict[str, Any]:
        """Map a FileMaker project record into SDK field names."""
        return {
            "id_primary": record.get(ProjectFields.ID_PRIMARY),
            "project_number": record.get(ProjectFields.PROJECT_NUMBER),
            "project_name": record.get(ProjectFields.PROJECT_NAME),
            "raw_fields": dict(record),
        }

    @staticmethod
    def _normalize_contract_record(record: Mapping[str, Any]) -> dict[str, Any]:
        """Map a FileMaker contract record into SDK field names."""
        return {
            "id_primary": record.get(ContractFields.ID_PRIMARY),
            "project_id_primary": record.get(ContractFields.PROJECT_ID),
            "contract_number": record.get(ContractFields.EFFECTIVE_CONTRACT_NUMBER),
            "legacy_contract_number": record.get(ContractFields.LEGACY_CONTRACT_NUMBER),
            "raw_fields": dict(record),
        }

    @staticmethod
    def _normalize_rfi_record(record: Mapping[str, Any]) -> dict[str, Any]:
        """Map a FileMaker RFI record into SDK field names."""
        return {
            "id_primary": record.get(RFIFields.ID_PRIMARY),
            "contract_id_primary": record.get(RFIFields.CONTRACT_ID),
            "rfi_number": record.get(RFIFields.RFI_NUMBER),
            "raw_fields": dict(record),
        }

    @staticmethod
    def _normalize_caan_record(record: Mapping[str, Any]) -> dict[str, Any]:
        """Map a FileMaker CAAN record into SDK field names."""
        return {
            "id_primary": record.get(CAANFields.ID_PRIMARY),
            "caan": record.get(CAANFields.CAAN),
            "name": record.get(CAANFields.NAME),
            "description": record.get(CAANFields.DESCRIPTION),
            "raw_fields": dict(record),
        }

    @staticmethod
    def _build_rfi_payload(
        rfi_data: Mapping[str, Any],
        *,
        contract_id_primary: Any | None = None,
    ) -> dict[str, Any]:
        """Normalize caller RFI keys into FileMaker field names."""
        payload = dict(rfi_data)
        resolved_contract_id = contract_id_primary or payload.get(
            "contract_id_primary",
            payload.get(RFIFields.CONTRACT_ID),
        )
        resolved_rfi_number = payload.get(
            "rfi_number",
            payload.get(RFIFields.RFI_NUMBER),
        )

        if not resolved_contract_id:
            raise FileMakerValidationError(
                "RFI payload must include contract_id_primary."
            )
        if not resolved_rfi_number:
            raise FileMakerValidationError(
                "RFI payload must include rfi_number."
            )

        payload[RFIFields.CONTRACT_ID] = resolved_contract_id
        payload[RFIFields.RFI_NUMBER] = resolved_rfi_number
        payload.pop("contract_id_primary", None)
        payload.pop("rfi_number", None)
        return payload

    @staticmethod
    def _rfi_number_duplicate_candidates(rfi_number: str) -> list[str]:
        """Return exact and leading-zero variants for duplicate checks."""
        candidates = [rfi_number]
        stripped = rfi_number.lstrip("0")
        if stripped and stripped != rfi_number:
            candidates.append(stripped)
        if rfi_number.isdigit() and not rfi_number.startswith("0"):
            candidates.append(rfi_number.zfill(5))
        return list(dict.fromkeys(candidates))

    @staticmethod
    def _dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove duplicate normalized records from multiple lookup passes."""
        deduped: list[dict[str, Any]] = []
        seen: set[Any] = set()
        for record in records:
            key = record.get("id_primary") or repr(sorted(record.items()))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(record)
        return deduped

    @staticmethod
    def _merge_criteria(
        base: Mapping[str, Any] | None,
        extra: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Merge caller criteria with named arguments and reject empties."""
        merged = dict(base or {})
        for key, value in extra.items():
            if value is not None:
                merged[key] = value
        if not merged:
            raise FileMakerValidationError("At least one search criterion is required.")
        return merged

    @staticmethod
    def _require_single_result(
        records: list[dict[str, Any]],
        label: str,
    ) -> dict[str, Any]:
        """Return one record, raising typed errors for zero or many."""
        if not records:
            raise FileMakerNotFoundError(f"No matching {label} found.")
        if len(records) > 1:
            raise FileMakerAmbiguousResultError(
                f"Expected a single {label}, but found {len(records)} matches."
            )
        return records[0]
