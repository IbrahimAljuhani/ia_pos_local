# Changelog — ia_pos_local

## [18.0.1.0.0] - 2026-03-17

### Added
- Initial release by Ibrahim Aljuhani (info@ia.sa)
- Mada payment via NeoLeap WebSocket — server-side connection (no IoT Box required)
- Full NeoLeap protocol: CHECK_STATUS → SALE → TERMINAL_RESPONSE
- StatusCode mapping: 00 approved / 01 bank decline / 11 customer cancel
- Manual payment fallback — cashier can enter approval code
- Multiple Mada terminals — one `neoleap_ip` per payment method
- Test Connection button for Mada terminals
- ESC/POS receipt printing over TCP — server sends image to printer
- Kitchen / order preparation printing over TCP
- Multiple printers — one `escpos_local_ip` + `escpos_local_port` per printer
- Test Connection button for printers
- Bilingual AR/EN messages in all JS components
- No IoT Box, no Raspberry Pi, no Mixed Content issues on http://

## [18.0.1.0.1] - 2026-03-17
### Changed
- Added `?? false` guard on `auto_validate_terminal_payment` — safe on both Community and Enterprise
- Updated summary to reflect Community & Enterprise compatibility
