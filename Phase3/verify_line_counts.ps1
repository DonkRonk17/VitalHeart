# Line Count Verification Script
# VitalHeart Phase 3 - HardwareSoul
# Purpose: Verify all claimed line counts against PowerShell Measure-Object
# Usage: powershell -ExecutionPolicy Bypass .\verify_line_counts.ps1

Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "  LINE COUNT VERIFICATION - VitalHeart Phase 3" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host ""

# Define files to verify
$files = @(
    "hardwaresoul.py",
    "test_hardwaresoul.py",
    "requirements.txt",
    "BUILD_COVERAGE_PLAN_PHASE3.md",
    "BUILD_AUDIT_PHASE3.md",
    "ARCHITECTURE_DESIGN_PHASE3.md",
    "BUG_HUNT_SEARCH_COVERAGE_PHASE3.md",
    "BUG_HUNT_REPORT_PHASE3.md",
    "README.md",
    "EXAMPLES.md",
    "QUALITY_GATES_REPORT.md",
    "BUILD_REPORT.md",
    "DEPLOYMENT.md",
    "PHASE3_COMPLETION_STATUS.md",
    "PHASE3_COMPLETE.txt",
    "BUILD_PROTOCOL_COMPLIANCE.md",
    "FORGE_REVIEW_FIXES_COMPLETE.md"
)

$totalLines = 0
$filesChecked = 0
$allPass = $true

Write-Host "Verifying line counts..." -ForegroundColor Yellow
Write-Host ""

foreach ($file in $files) {
    if (Test-Path $file) {
        $actualLines = (Get-Content $file | Measure-Object -Line).Lines
        $totalLines += $actualLines
        $filesChecked++
        
        Write-Host "[OK] " -NoNewline -ForegroundColor Green
        Write-Host "$file : " -NoNewline
        Write-Host "$actualLines lines" -ForegroundColor Cyan
    } else {
        Write-Host "[MISSING] " -NoNewline -ForegroundColor Red
        Write-Host "$file : " -NoNewline
        Write-Host "FILE NOT FOUND" -ForegroundColor Red
        $allPass = $false
    }
}

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "SUMMARY" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "Files Checked: $filesChecked / $($files.Count)" -ForegroundColor White
Write-Host "Total Lines: $totalLines" -ForegroundColor White

if ($allPass) {
    Write-Host "Status: ALL FILES VERIFIED" -ForegroundColor Green
} else {
    Write-Host "Status: MISSING FILES DETECTED" -ForegroundColor Red
}

Write-Host ""
Write-Host "Verification Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

# Compare against expected total (BUILD_REPORT.md claim)
$expectedTotal = 6001
$delta = $totalLines - $expectedTotal

if ($delta -eq 0) {
    Write-Host "Line count matches BUILD_REPORT.md ($expectedTotal lines)" -ForegroundColor Green
} elseif ($delta -gt 0) {
    Write-Host "Line count is $delta lines MORE than BUILD_REPORT.md ($expectedTotal)" -ForegroundColor Yellow
    Write-Host "ACTION REQUIRED: Update BUILD_REPORT.md with $totalLines total" -ForegroundColor Yellow
} else {
    Write-Host "Line count is $([Math]::Abs($delta)) lines LESS than BUILD_REPORT.md ($expectedTotal)" -ForegroundColor Yellow
    Write-Host "ACTION REQUIRED: Update BUILD_REPORT.md with $totalLines total" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "===============================================================" -ForegroundColor Cyan
Write-Host "For the Maximum Benefit of Life - Team Brain" -ForegroundColor Cyan
Write-Host "===============================================================" -ForegroundColor Cyan
