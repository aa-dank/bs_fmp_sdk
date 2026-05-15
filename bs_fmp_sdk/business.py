from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .client import FileMakerClient
from .exceptions import (
    FileMakerAmbiguousResultError,
    FileMakerDuplicateError,
    FileMakerNotFoundError,
    FileMakerValidationError,
)
from .layouts import ContractFields, Layouts, ProjectFields, RFIFields


class BusinessServicesFileMakerClient:
    """
    Higher-level business client for the UCSC Business Services FileMaker app.

    Public lookup methods are intentionally exposed because they are useful as
    standalone SDK operations in scripts, spreadsheets, and notebooks.
    """

    def __init__(self, client: FileMakerClient) -> None:
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
        merged_criteria = self._merge_criteria(
            criteria,
            {
                ProjectFields.ID_PRIMARY: id_primary,
                ProjectFields.PROJECT_NUMBER: project_number,
                ProjectFields.PROJECT_NAME: project_name,
            },
        )
        return self.client.find_matching(
            merged_criteria,
            layout_name=Layouts.PROJECTS,
            limit=limit,
        )

    def get_project(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        project_number: str | None = None,
        project_name: str | None = None,
        id_primary: str | None = None,
    ) -> dict[str, Any]:
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
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        merged_criteria = self._merge_criteria(
            criteria,
            {
                ContractFields.PROJECT_ID: project_id_primary,
                ContractFields.PROJECT_NUMBER_LOOKUP: project_number,
                ContractFields.CONTRACT_NUMBER: contract_number,
            },
        )
        return self.client.find_matching(
            merged_criteria,
            layout_name=Layouts.CONTRACTS,
            limit=limit,
        )

    def get_contract(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        project_id_primary: str | None = None,
        project_number: str | None = None,
        contract_number: str | None = None,
    ) -> dict[str, Any]:
        records = self.find_contracts(
            criteria=criteria,
            project_id_primary=project_id_primary,
            project_number=project_number,
            contract_number=contract_number,
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
        resolved_project = dict(project) if project is not None else self.get_project(criteria=project_criteria)
        project_id_primary = resolved_project.get(ProjectFields.ID_PRIMARY)
        if not project_id_primary:
            raise FileMakerValidationError(
                f"Resolved project is missing required field '{ProjectFields.ID_PRIMARY}'."
            )

        records = self.find_contracts(
            criteria=contract_criteria,
            project_id_primary=str(project_id_primary),
            limit=10,
        )
        return self._require_single_result(records, "contract")

    def find_rfis(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        contract_id_primary: str | None = None,
        rfi_number: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        merged_criteria = self._merge_criteria(
            criteria,
            {
                RFIFields.CONTRACT_ID: contract_id_primary,
                RFIFields.RFI_NUMBER: rfi_number,
            },
        )
        return self.client.find_matching(
            merged_criteria,
            layout_name=Layouts.RFIS,
            limit=limit,
        )

    def get_rfi(
        self,
        *,
        criteria: Mapping[str, Any] | None = None,
        contract_id_primary: str | None = None,
        rfi_number: str | None = None,
    ) -> dict[str, Any]:
        records = self.find_rfis(
            criteria=criteria,
            contract_id_primary=contract_id_primary,
            rfi_number=rfi_number,
            limit=10,
        )
        return self._require_single_result(records, "RFI")

    def create_rfi(
        self,
        rfi_data: Mapping[str, Any],
        *,
        allow_duplicate: bool = False,
    ) -> Any:
        payload = dict(rfi_data)
        contract_id_primary = payload.get(RFIFields.CONTRACT_ID)
        rfi_number = payload.get(RFIFields.RFI_NUMBER)

        if not contract_id_primary:
            raise FileMakerValidationError(
                f"RFI payload must include '{RFIFields.CONTRACT_ID}'."
            )
        if not rfi_number:
            raise FileMakerValidationError(
                f"RFI payload must include '{RFIFields.RFI_NUMBER}'."
            )

        if not allow_duplicate:
            existing = self.find_rfis(
                contract_id_primary=str(contract_id_primary),
                rfi_number=str(rfi_number),
                limit=5,
            )
            if existing:
                raise FileMakerDuplicateError(
                    f"An RFI already exists for contract '{contract_id_primary}' with number '{rfi_number}'."
                )

        return self.client.create_record(payload, layout_name=Layouts.RFIS)

    def create_rfi_for_project(
        self,
        *,
        project_criteria: Mapping[str, Any],
        rfi_data: Mapping[str, Any],
        contract_criteria: Mapping[str, Any] | None = None,
    ) -> Any:
        resolved_project = self.get_project(criteria=project_criteria)
        resolved_contract = self.get_contract_for_project(
            project=resolved_project,
            contract_criteria=contract_criteria,
        )

        contract_id_primary = resolved_contract.get(ContractFields.ID_PRIMARY)
        if not contract_id_primary:
            raise FileMakerValidationError(
                f"Resolved contract is missing required field '{ContractFields.ID_PRIMARY}'."
            )

        payload = dict(rfi_data)
        payload[RFIFields.CONTRACT_ID] = contract_id_primary
        return self.create_rfi(payload, allow_duplicate=False)

    @staticmethod
    def _merge_criteria(
        base: Mapping[str, Any] | None,
        extra: Mapping[str, Any],
    ) -> dict[str, Any]:
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
        if not records:
            raise FileMakerNotFoundError(f"No matching {label} found.")
        if len(records) > 1:
            raise FileMakerAmbiguousResultError(
                f"Expected a single {label}, but found {len(records)} matches."
            )
        return records[0]
