from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from .business import BusinessServicesFileMakerClient
from .client import FileMakerClient
from .config import load_config
from .exceptions import FileMakerError


JsonDict = dict[str, Any]


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        result = _dispatch(args)
        _write_json({"ok": True, "result": result})
        return 0
    except Exception as exc:
        _write_json(
            {
                "ok": False,
                "error": {
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "is_filemaker_error": isinstance(exc, FileMakerError),
                },
            },
            stream=sys.stderr,
        )
        return 1


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bs-fmp",
        description="JSON command wrapper for UCSC Business Services FileMaker operations.",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=None,
        help="Optional .env path. Defaults to the SDK repo .env.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("ping", help="Check FileMaker connectivity.")

    find_projects = subparsers.add_parser("find-projects", help="Find project records.")
    _add_common_lookup_args(find_projects)
    find_projects.add_argument("--project-number")
    find_projects.add_argument("--project-name")
    find_projects.add_argument("--id-primary")

    get_project = subparsers.add_parser("get-project", help="Get exactly one project.")
    _add_common_lookup_args(get_project, include_limit=False)
    get_project.add_argument("--project-number")
    get_project.add_argument("--project-name")
    get_project.add_argument("--id-primary")

    find_contracts = subparsers.add_parser("find-contracts", help="Find contract records.")
    _add_common_lookup_args(find_contracts)
    find_contracts.add_argument("--project-id-primary")
    find_contracts.add_argument("--project-number")
    find_contracts.add_argument("--contract-number")
    find_contracts.add_argument("--raw-contract-number")

    find_rfis = subparsers.add_parser("find-rfis", help="Find RFI records.")
    _add_common_lookup_args(find_rfis)
    find_rfis.add_argument("--contract-id-primary")
    find_rfis.add_argument("--rfi-number")

    create_rfi = subparsers.add_parser("create-rfi", help="Create an RFI by contract ID.")
    create_rfi.add_argument("--payload", required=True, help="JSON object with RFI field data.")
    create_rfi.add_argument("--allow-duplicate", action="store_true")
    create_rfi.add_argument("--commit", action="store_true", help="Actually write to FileMaker.")

    create_project_rfi = subparsers.add_parser(
        "create-rfi-for-project",
        help="Resolve project/contract and create an RFI.",
    )
    create_project_rfi.add_argument(
        "--project-criteria",
        required=True,
        help="JSON object used to resolve exactly one project.",
    )
    create_project_rfi.add_argument("--rfi-data", required=True, help="JSON object with RFI field data.")
    create_project_rfi.add_argument(
        "--contract-criteria",
        default=None,
        help="Optional JSON object used while resolving the project contract.",
    )
    create_project_rfi.add_argument("--commit", action="store_true", help="Actually write to FileMaker.")

    edit_record = subparsers.add_parser("edit-record", help="Edit a FileMaker record by layout and recordId.")
    edit_record.add_argument("--layout", required=True, help="FileMaker layout name.")
    edit_record.add_argument("--record-id", required=True, help="FileMaker recordId, not ID_Primary.")
    edit_record.add_argument("--payload", required=True, help="JSON object with field data to update.")
    edit_record.add_argument("--commit", action="store_true", help="Actually write to FileMaker.")

    delete_record = subparsers.add_parser("delete-record", help="Delete a FileMaker record by layout and recordId.")
    delete_record.add_argument("--layout", required=True, help="FileMaker layout name.")
    delete_record.add_argument("--record-id", required=True, help="FileMaker recordId, not ID_Primary.")
    delete_record.add_argument("--commit", action="store_true", help="Actually delete from FileMaker.")

    return parser


def _add_common_lookup_args(
    parser: argparse.ArgumentParser,
    *,
    include_limit: bool = True,
) -> None:
    parser.add_argument("--criteria", default=None, help="Optional JSON object with raw FileMaker criteria.")
    if include_limit:
        parser.add_argument("--limit", type=int, default=None)


def _dispatch(args: argparse.Namespace) -> Any:
    write_commands = {"create-rfi", "create-rfi-for-project", "edit-record", "delete-record"}
    if args.command in write_commands and not args.commit:
        return _preview_write(args)

    raw = FileMakerClient(load_config(args.env_file))
    sdk = BusinessServicesFileMakerClient(raw)

    handlers: dict[str, Callable[[BusinessServicesFileMakerClient, argparse.Namespace], Any]] = {
        "ping": _ping,
        "find-projects": _find_projects,
        "get-project": _get_project,
        "find-contracts": _find_contracts,
        "find-rfis": _find_rfis,
        "create-rfi": _create_rfi,
        "create-rfi-for-project": _create_rfi_for_project,
        "edit-record": _edit_record,
        "delete-record": _delete_record,
    }

    try:
        return handlers[args.command](sdk, args)
    finally:
        raw.logout()


def _preview_write(args: argparse.Namespace) -> JsonDict:
    if args.command == "create-rfi":
        payload = _require_json_object(args.payload, "--payload")
        return {
            "dry_run": True,
            "preview": {
                "operation": "create-rfi",
                "commit": False,
                "allow_duplicate": args.allow_duplicate,
                "payload": payload,
            },
        }

    if args.command == "edit-record":
        payload = _require_json_object(args.payload, "--payload")
        return {
            "dry_run": True,
            "preview": {
                "operation": "edit-record",
                "commit": False,
                "layout": args.layout,
                "record_id": args.record_id,
                "payload": payload,
            },
        }

    if args.command == "delete-record":
        return {
            "dry_run": True,
            "preview": {
                "operation": "delete-record",
                "commit": False,
                "layout": args.layout,
                "record_id": args.record_id,
            },
        }

    project_criteria = _require_json_object(args.project_criteria, "--project-criteria")
    rfi_data = _require_json_object(args.rfi_data, "--rfi-data")
    contract_criteria = _json_arg(args.contract_criteria)
    return {
        "dry_run": True,
        "preview": {
            "operation": "create-rfi-for-project",
            "commit": False,
            "project_criteria": project_criteria,
            "contract_criteria": contract_criteria,
            "rfi_data": rfi_data,
        },
    }


def _ping(sdk: BusinessServicesFileMakerClient, args: argparse.Namespace) -> JsonDict:
    return {"connected": sdk.client.ping()}


def _find_projects(sdk: BusinessServicesFileMakerClient, args: argparse.Namespace) -> list[JsonDict]:
    return sdk.find_projects(
        criteria=_json_arg(args.criteria),
        project_number=args.project_number,
        project_name=args.project_name,
        id_primary=args.id_primary,
        limit=args.limit,
    )


def _get_project(sdk: BusinessServicesFileMakerClient, args: argparse.Namespace) -> JsonDict:
    return sdk.get_project(
        criteria=_json_arg(args.criteria),
        project_number=args.project_number,
        project_name=args.project_name,
        id_primary=args.id_primary,
    )


def _find_contracts(sdk: BusinessServicesFileMakerClient, args: argparse.Namespace) -> list[JsonDict]:
    return sdk.find_contracts(
        criteria=_json_arg(args.criteria),
        project_id_primary=args.project_id_primary,
        project_number=args.project_number,
        contract_number=args.contract_number,
        raw_contract_number=args.raw_contract_number,
        limit=args.limit,
    )


def _find_rfis(sdk: BusinessServicesFileMakerClient, args: argparse.Namespace) -> list[JsonDict]:
    return sdk.find_rfis(
        criteria=_json_arg(args.criteria),
        contract_id_primary=args.contract_id_primary,
        rfi_number=args.rfi_number,
        limit=args.limit,
    )


def _create_rfi(sdk: BusinessServicesFileMakerClient, args: argparse.Namespace) -> JsonDict:
    payload = _require_json_object(args.payload, "--payload")
    preview = {
        "operation": "create-rfi",
        "commit": args.commit,
        "allow_duplicate": args.allow_duplicate,
        "payload": payload,
    }
    if not args.commit:
        return {"dry_run": True, "preview": preview}

    return {"dry_run": False, "preview": preview, "response": sdk.create_rfi(payload, allow_duplicate=args.allow_duplicate)}


def _create_rfi_for_project(sdk: BusinessServicesFileMakerClient, args: argparse.Namespace) -> JsonDict:
    project_criteria = _require_json_object(args.project_criteria, "--project-criteria")
    rfi_data = _require_json_object(args.rfi_data, "--rfi-data")
    contract_criteria = _json_arg(args.contract_criteria)

    preview = {
        "operation": "create-rfi-for-project",
        "commit": args.commit,
        "project_criteria": project_criteria,
        "contract_criteria": contract_criteria,
        "rfi_data": rfi_data,
    }
    if not args.commit:
        return {"dry_run": True, "preview": preview}

    response = sdk.create_rfi_for_project(
        project_criteria=project_criteria,
        contract_criteria=contract_criteria,
        rfi_data=rfi_data,
    )
    return {"dry_run": False, "preview": preview, "response": response}


def _edit_record(sdk: BusinessServicesFileMakerClient, args: argparse.Namespace) -> JsonDict:
    payload = _require_json_object(args.payload, "--payload")
    preview = {
        "operation": "edit-record",
        "commit": args.commit,
        "layout": args.layout,
        "record_id": args.record_id,
        "payload": payload,
    }
    response = sdk.client.edit_record(args.record_id, payload, layout_name=args.layout)
    return {"dry_run": False, "preview": preview, "response": response}


def _delete_record(sdk: BusinessServicesFileMakerClient, args: argparse.Namespace) -> JsonDict:
    preview = {
        "operation": "delete-record",
        "commit": args.commit,
        "layout": args.layout,
        "record_id": args.record_id,
    }
    response = sdk.client.delete_record(args.record_id, layout_name=args.layout)
    return {"dry_run": False, "preview": preview, "response": response}


def _json_arg(value: str | None) -> JsonDict | None:
    if value is None:
        return None
    return _require_json_object(value, "JSON argument")


def _require_json_object(value: str, label: str) -> JsonDict:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return parsed


def _write_json(payload: Mapping[str, Any], *, stream: Any = sys.stdout) -> None:
    json.dump(payload, stream, indent=2, sort_keys=True, default=str)
    stream.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
