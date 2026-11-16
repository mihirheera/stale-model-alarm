# Feature audit

Prediction point simulated: **the day the SBA guarantee is approved.** A feature is allowed only if a
bank would know it on that day. Definitions follow Li, Mickel & Taylor (2018), Table 1(a).

| Raw column | Meaning | Known at approval? | Leakage risk | Decision | Why |
|---|---|---|---|---|---|
| LoanNr_ChkDgt | Loan ID | Yes | None, but meaningless | Remove | An identifier carries no risk information. |
| Name | Borrower name | Yes | Privacy; could act as a proxy | Remove | Never used. I do not infer anything from names. |
| City, Zip | Location | Yes | Very many values; privacy | Remove | Too fine-grained; `State` is kept instead. |
| State | Borrower state | Yes | Low | **Keep** (`state`) | Regional economy matters. |
| Bank | Lender name | Yes | High-cardinality ID | Remove | Would let the model memorise lenders. |
| BankState | Lender state | Yes | Low | **Keep** as `same_state` | Whether the bank is in the borrower's state. |
| NAICS | Industry code | Yes | Low; missing before FY2001 | **Keep** first 2 digits (`sector`, "00" = not recorded) | Industry risk differs. |
| ApprovalDate / ApprovalFY | Approval date / fiscal year | Yes | Using it as a feature would let the model learn the year | Use **only to split data by time**, never as a feature | Prevents learning "later year = riskier". |
| Term | Loan length (months) | Should be | **High (see decision D1)** | **Remove** (incl. RealEstate flag) | Odd terms default 30× more often than round terms in mature cohorts. |
| NoEmp | Employees | Yes | Low | **Keep** (`no_emp`, log scale) | Business size. |
| NewExist | New (≤2 yrs) vs existing | Yes | Low | **Keep** (`new_business`, unknown kept as its own value) | Start-ups may be riskier. |
| CreateJob / RetainedJob | Jobs the loan should create / keep | Yes (stated in application) | Low | **Keep** (log scale) | Describes the loan's purpose and size. |
| FranchiseCode | Franchise ID (0/1 = none) | Yes | Low | **Keep** as yes/no (`franchise`) | Franchises have a known business model. |
| UrbanRural | 1 urban, 2 rural, 0 undefined | Yes | Recording changes over time | **Keep** (`urban_rural`) | Checked in robustness E7. |
| RevLineCr | Revolving credit line Y/N | Yes | Many invalid codes | **Keep** (`revline`, Y/N/unknown) | Checked in robustness E7. |
| LowDoc | One-page application program | Yes | Program stopped ~FY2006 | **Keep** (`lowdoc`) | A real policy change, discussed separately. |
| DisbursementDate | When money was paid out | Shortly after approval | Low, but after the prediction point | Not a feature; used for maturity analysis | Keeps the prediction point clean. |
| DisbursementGross | Amount paid out | Shortly after approval | Low | Not a feature | `GrAppv` (approved amount) is used instead. |
| GrAppv | Gross amount approved | Yes | Low | **Keep** (`log_amount`) | Loan size. |
| SBA_Appv | SBA-guaranteed amount | Yes | Low | **Keep** as `sba_share` = SBA_Appv / GrAppv | Guarantee share (Li et al. 4.1.7). |
| BalanceGross | Amount still outstanding | **No** (current balance) | **High** | **Remove** | Describes the loan after the fact. |
| ChgOffDate | Date declared in default | **No** | **Direct leak** | **Remove** as a feature; used only by the label-based monitor at the time it would actually be known | Exists only for defaulted loans. |
| ChgOffPrinGr | Amount charged off | **No** | **Direct leak** | **Remove** | Positive almost only for defaults. |
| MIS_Status | CHGOFF / PIF | **No (the outcome)** | It *is* the target | Target only (`y`); missing → excluded, never assumed repaid | 1,997 loans have no status. |
