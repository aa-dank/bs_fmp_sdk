# Warranty deficiency notes

## Layouts
Preferred import layout:
- `ImportWarrDef`

Other observed layouts:
- `warranty_defficiency_table` targets `WarrantyDeficiency`; note the layout spelling.
- `WarrantyDeficiencyDetail` is a user/detail layout with related display fields.
- `WD Official Notice` and `WD Action Report` also target `WarrantyDeficiency`.
- `ImportWDTracking` targets `WarrantyDeficiencyTracking`.

`ImportWarrDef` and `warranty_defficiency_table` expose the same 61 fields in the current FileMaker Data API metadata.

## Core table fields
Business-facing writable fields observed on `ImportWarrDef`:
- `ProjectNumber` text
- `ID_WD` number, auto-entered, appears to be the warranty deficiency number within a project rather than a globally unique business key
- `DateReported` date
- `Location` text
- `NatureOfDeficiency` text
- `ID_ReportedBy` number, links to `People::ID_Primary`
- `ReportedVia` text
- `ReviewDate` date
- `ID_ReviewedBy` number, links to `People::ID_Primary`
- `ReviewComments` text
- `InspectorReviewStatus` text
- `DateSignedOff` date
- `ID_SignedOffBy` number, links to `People::ID_Primary`
- `Closed` text
- `Comments` text

Additional normal writable fields that appear workflow/email related:
- `CompletionConfirmationCommentsAdd`
- `OfficialCommentsAdd`
- `RequestReviewCommentsAdd`
- `ReviewCompleteCommentsAdd`
- `EmailBody_CompletionConfirmation`
- `EmailBody_OfficialNotice`
- `EmailBody_RequestReview`
- `EmailBody_ReviewComplete`
- `EmailBody_WorkCorrected`
- `EmailText_NotifyPPC`

Contractor signoff fields are present but appear unused in current data inspected 2026-06-25:
- `ContractorSignoff`
- `ContractorSignoffComments`
- `ContractorSignoffDate`
- `ID_ContractorSignoff`

Auto-enter and system fields:
- `ID_Primary`
- `ID_WD`
- `Constant`
- `z_CreatedBy`
- `z_CreatedTimestamp`
- `z_CreationDate`
- `z_LogData`
- `z_ModificationDate`
- `z_ModificationTimestamp`
- `z_ModifiedBy`

Calculation or summary fields should not be supplied in create/update payloads:
- `Complete`
- `CompleteOLD`
- `Constant_count`
- `EmailBody_CompletionConfirmation_c`
- `EmailBody_OfficialNotice_c`
- `EmailBody_PlantClosedOut`
- `EmailBody_RequestReview_c`
- `EmailBody_ReviewComplete_c`
- `EmailBody_ReviewInvalid`
- `EmailBody_ReviewValid`
- `EmailBody_WorkCorrected_c`
- `EmailSubject_CompletionConfirmation`
- `EmailSubject_NotifyPPC`
- `EmailSubject_OfficialNotice`
- `EmailSubject_RequestReview_c`
- `EmailSubject_ReviewComplete_c`
- `EmailSubject_WorkCorrected_c`
- `LastAction`
- `NewRecordEmailText`
- `PlantSubmitText`
- `WDNumberMax_c`
- `z_RecordID`

## Person relationships
`WarrantyDeficiencyDetail` confirms these related display fields:
- `WD Reported::NameFirstMiddleLast` corresponds to `ID_ReportedBy`
- `WD Reviewed::NameFirstMiddleLast` corresponds to `ID_ReviewedBy`
- `WD UC SignOff::NameFirstMiddleLast` corresponds to `ID_SignedOffBy`

People IDs should resolve through `ImportPeople` using `People::ID_Primary`. Useful people lookup fields on `ImportPeople` include:
- `ID_Primary`
- `NameFirst`
- `NameLast`
- `NameFirstMiddleLast`
- `NameFirstLast_c`
- `NameFirstLastCompany`
- `Email`
- `Email2`
- `Company`
- `Inactive`

For SDK workflows, exact matches should be preferred for person resolution. If an exact match is missing or ambiguous, return candidate people for review rather than silently choosing the wrong `ID_Primary`.

## Observed values and uniqueness
Observed on 2026-06-25 from `ImportWarrDef`:
- `InspectorReviewStatus` mostly uses `Valid`, `Invalid`, `In Process - More Info Needed`, and `Not Reviewed`; there is at least one free-text legacy value.
- `Closed` is usually blank; closed records generally use `Closed`, with at least one legacy dirty value.
- `ReportedVia` is free text with inconsistent capitalization and wording.
- `ContractorSignoff` was blank on all inspected records.

`ID_WD` is not globally unique. Treat the likely business uniqueness key as `ProjectNumber` + `ID_WD`, while keeping in mind that a small number of duplicate combinations exist in historical data.
