// script.js - Client side logic, drag & drop, dynamic HRA rows, and API requests

window.onerror = function(message, source, lineno, colno, error) {
    alert("JS Debug Error: " + message + "\nLine: " + lineno + "\nSource: " + source);
    return false;
};

document.addEventListener("DOMContentLoaded", () => {
    // Determine API Base URL depending on where the page is hosted
    const DEFAULT_DA_RATES = [
        { from_month: "2023-01", to_month: "2023-12", rate_percent: 46 },
        { from_month: "2024-01", to_month: "2024-06", rate_percent: 50 },
        { from_month: "2024-07", to_month: "2024-12", rate_percent: 53 },
        { from_month: "2025-01", to_month: "2025-06", rate_percent: 55 },
        { from_month: "2025-07", to_month: "2025-12", rate_percent: 58 },
        { from_month: "2026-01", to_month: "2026-06", rate_percent: 60 },
    ];

    let API_BASE_URL = "";
    if (window.location.hostname !== "127.0.0.1" && 
        window.location.hostname !== "localhost" && 
        !window.location.hostname.includes("onrender.com")) {
        API_BASE_URL = "https://arrear-backend.onrender.com";
    }

    // Files tracking object
    const files = {}; // key: form field name (e.g., "yearly_pdf_0"), value: File object

    const btnSubmit = document.getElementById("btn-submit");
    const btnAddHra = document.getElementById("btn-add-hra");
    const hraPresets = document.getElementById("hra-presets");
    const hraTableBody = document.getElementById("hra-table-body");
    const arrearForm = document.getElementById("arrear-form");

    // Progress Bar DOM Elements
    const progressContainer = document.getElementById("progress-container");
    const progressStatus = document.getElementById("progress-status");
    const progressPercent = document.getElementById("progress-percent");
    const progressBarFill = document.getElementById("progress-bar-fill");
    let progressInterval = null;

    function startProgressBar(initialMsg) {
        progressContainer.style.display = "block";
        progressBarFill.style.width = "0%";
        progressBarFill.style.background = "linear-gradient(90deg, var(--primary-color), #8b5cf6)";
        progressBarFill.style.boxShadow = "0 0 10px rgba(99, 102, 241, 0.5)";
        progressPercent.textContent = "0%";
        progressStatus.textContent = initialMsg;

        let percent = 0;
        const steps = [
            { limit: 25, msg: "Uploading HRMS files..." },
            { limit: 50, msg: "Analyzing salary slips & statements..." },
            { limit: 75, msg: "Calculating admissible pay rate slabs..." },
            { limit: 95, msg: "Compiling Excel formulas & layout..." }
        ];

        let currentStepIndex = 0;
        clearInterval(progressInterval);
        progressInterval = setInterval(() => {
            if (currentStepIndex >= steps.length) {
                clearInterval(progressInterval);
                return;
            }

            const currentStep = steps[currentStepIndex];
            percent += 1;

            progressBarFill.style.width = percent + "%";
            progressPercent.textContent = percent + "%";
            progressStatus.textContent = currentStep.msg;

            if (percent >= currentStep.limit) {
                currentStepIndex++;
            }
        }, 120);
    }

    function finishProgressBar(successMsg) {
        clearInterval(progressInterval);
        progressBarFill.style.width = "100%";
        progressPercent.textContent = "100%";
        progressStatus.textContent = successMsg;

        setTimeout(() => {
            progressContainer.style.display = "none";
        }, 3000);
    }

    function failProgressBar(errorMsg) {
        clearInterval(progressInterval);
        progressBarFill.style.width = "100%";
        progressBarFill.style.background = "#ef4444";
        progressBarFill.style.boxShadow = "0 0 10px rgba(239, 68, 68, 0.5)";
        progressPercent.textContent = "Error";
        progressStatus.textContent = errorMsg;
    }

    // Preview Panel Elements
    const previewPlaceholder = document.getElementById("preview-placeholder");
    const previewContent = document.getElementById("preview-content");
    const warningBox = document.getElementById("warning-box");
    const previewName = document.getElementById("preview-name");
    const previewDesig = document.getElementById("preview-desig");
    const previewStep = document.getElementById("preview-step");
    const previewDoj = document.getElementById("preview-doj");
    const previewPran = document.getElementById("preview-pran");
    const previewPan = document.getElementById("preview-pan");
    const previewIncMonth = document.getElementById("preview-inc-month");
    const previewTotalArrear = document.getElementById("preview-total-arrear");
    const previewInWords = document.getElementById("preview-in-words");
    const previewTableBody = document.getElementById("preview-table-body");

    // Dynamic Upload Slots and DA Table Logic
    function calculateFinancialYears(startStr, endStr) {
        const startParts = startStr.split("-");
        const endParts = endStr.split("-");
        const startYear = parseInt(startParts[0]);
        const startMonth = parseInt(startParts[1]);
        const endYear = parseInt(endParts[0]);
        const endMonth = parseInt(endParts[1]);
        
        const fys = [];
        let fyStartYear = startMonth >= 3 ? startYear : startYear - 1;
        let fyEndYear = endMonth >= 3 ? endYear : endYear - 1;
        
        for (let y = fyStartYear; y <= fyEndYear; y++) {
            fys.push({
                label: `${y}-${String(y + 1).slice(-2)}`,
                displayLabel: `Yearly Statement ${y}-${String(y + 1).slice(-2)}`
            });
        }
        return fys;
    }

    function regenerateUploadSlots() {
        const startVal = document.getElementById("scope-start").value;
        const endVal = document.getElementById("scope-end").value;
        const fys = calculateFinancialYears(startVal, endVal);
        
        document.getElementById("scope-info").textContent = 
            `Covers ${fys.length} financial year${fys.length > 1 ? 's' : ''}: ${fys.map(f => f.label).join(", ")}`;
        
        const grid = document.getElementById("upload-grid");
        grid.innerHTML = "";
        
        document.querySelectorAll("input[id^='file-yp-']").forEach(el => el.remove());
        
        Object.keys(files).forEach(k => { if (k.startsWith("yearly_pdf_")) delete files[k]; });
        
        fys.forEach((fy, idx) => {
            const fieldName = `yearly_pdf_${idx}`;
            
            const dz = document.createElement("div");
            dz.className = "drop-zone";
            dz.id = `dz-yp-${idx}`;
            dz.innerHTML = `
                <span class="drop-zone-icon">📄</span>
                <span class="drop-zone-title">${fy.displayLabel}</span>
                <span class="drop-zone-desc">Drag & drop PDF or click to browse</span>
                <div class="file-name-badge" id="name-yp-${idx}"></div>
            `;
            grid.appendChild(dz);
            
            const input = document.createElement("input");
            input.type = "file";
            input.name = fieldName;
            input.id = `file-yp-${idx}`;
            input.accept = "application/pdf";
            input.style.cssText = "opacity: 0; position: absolute; width: 0; height: 0; pointer-events: none;";
            grid.appendChild(input);
            
            setupDropZone(dz, input, fieldName, `name-yp-${idx}`);
        });
        
        updateButtonStates();
    }

    function setupDropZone(dropZone, fileInput, fieldName, badgeId) {
        fileInput.addEventListener("click", (e) => e.stopPropagation());
        dropZone.addEventListener("click", (e) => {
            e.stopPropagation();
            fileInput.click();
        });
        
        dropZone.addEventListener("dragover", (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });
        
        dropZone.addEventListener("dragleave", () => {
            dropZone.classList.remove("dragover");
        });
        
        dropZone.addEventListener("drop", (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                handleFile(e.dataTransfer.files[0], fieldName, badgeId, dropZone);
            }
        });
        
        fileInput.addEventListener("change", () => {
            if (fileInput.files.length > 0) {
                handleFile(fileInput.files[0], fieldName, badgeId, dropZone);
            }
        });
    }

    function handleFile(file, fieldName, badgeId, dropZone) {
        if (file.type !== "application/pdf") {
            alert("Please upload a PDF file.");
            return;
        }
        files[fieldName] = file;
        const badge = document.getElementById(badgeId);
        if (badge) {
            badge.textContent = file.name;
            badge.style.display = "block";
        }
        dropZone.classList.add("file-loaded");
        updateButtonStates();
    }

    function updateButtonStates() {
        const yearlySlots = document.querySelectorAll("[id^='dz-yp-']");
        const yearlyCount = yearlySlots.length;
        let yearlyFilled = 0;
        for (let i = 0; i < yearlyCount; i++) {
            if (files[`yearly_pdf_${i}`]) yearlyFilled++;
        }
        const hasPayslip = !!files["payslip_pdf"];
        const allReady = yearlyFilled === yearlyCount && hasPayslip && yearlyCount > 0;
        
        btnSubmit.disabled = !allReady;
    }

    function initDaTable() {
        const tbody = document.getElementById("da-table-body");
        tbody.innerHTML = "";
        DEFAULT_DA_RATES.forEach(rate => {
            addDaRow(rate.from_month, rate.to_month, rate.rate_percent);
        });
    }

    function addDaRow(from = "", to = "", rate = "") {
        const tbody = document.getElementById("da-table-body");
        const row = document.createElement("tr");
        row.innerHTML = `
            <td><input type="month" value="${from}" class="da-from"></td>
            <td><input type="month" value="${to}" class="da-to"></td>
            <td><input type="number" value="${rate}" step="0.5" min="0" max="100" class="da-rate" placeholder="e.g. 46"></td>
            <td><button type="button" class="btn btn-danger btn-sm da-remove">✕</button></td>
        `;
        row.querySelector(".da-remove").addEventListener("click", () => row.remove());
        tbody.appendChild(row);
    }

    function getDaRatesData() {
        const list = [];
        document.querySelectorAll("#da-table-body tr").forEach(row => {
            const from = row.querySelector(".da-from").value;
            const to = row.querySelector(".da-to").value;
            const rate = parseFloat(row.querySelector(".da-rate").value);
            if (from && to && !isNaN(rate)) {
                list.push({ from_month: from, to_month: to, rate_percent: rate });
            }
        });
        return list;
    }

    document.getElementById("btn-add-da").addEventListener("click", () => addDaRow());
    document.getElementById("da-presets").addEventListener("change", (e) => {
        if (e.target.value === "standard") {
            initDaTable();
        } else {
            document.getElementById("da-table-body").innerHTML = "";
            addDaRow();
        }
    });

    document.getElementById("scope-start").addEventListener("change", regenerateUploadSlots);
    document.getElementById("scope-end").addEventListener("change", regenerateUploadSlots);

    // Initial setups
    initDaTable();
    setupDropZone(document.getElementById("dz-ps"), document.getElementById("file-ps"), "payslip_pdf", "name-ps");
    regenerateUploadSlots();

    // Dynamic HRA Table Operations
    function createHraRow(fromVal = "", toVal = "", rateVal = "") {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td><input type="text" class="hra-from" placeholder="E.g., 2023-11" value="${fromVal}" required></td>
            <td><input type="text" class="hra-to" placeholder="E.g., 2023-12" value="${toVal}" required></td>
            <td><input type="number" step="0.1" class="hra-rate" placeholder="Rate %" value="${rateVal}" required style="width: 80px;"></td>
            <td><button type="button" class="btn btn-danger btn-sm btn-delete-row">Remove</button></td>
        `;
        
        tr.querySelector(".btn-delete-row").addEventListener("click", () => {
            tr.remove();
        });
        
        return tr;
    }

    btnAddHra.addEventListener("click", () => {
        hraTableBody.appendChild(createHraRow());
    });

    // HRA Preset Management
    hraPresets.addEventListener("change", (e) => {
        const val = e.target.value;
        hraTableBody.innerHTML = ""; // clear
        
        if (val === "4to5") {
            hraTableBody.appendChild(createHraRow("2023-11", "2023-12", "4.0"));
            hraTableBody.appendChild(createHraRow("2024-01", "2026-12", "5.0"));
        } else if (val === "7.5to10") {
            hraTableBody.appendChild(createHraRow("2023-11", "2023-12", "7.5"));
            hraTableBody.appendChild(createHraRow("2024-01", "2026-12", "10.0"));
        } else if (val === "corrected") {
            // New joiner defaulted to 4% but school is 7.5% -> 10%
            // Admissible was 7.5% until Dec-23, then 10% from Jan-24 onwards
            hraTableBody.appendChild(createHraRow("2023-11", "2023-12", "7.5"));
            hraTableBody.appendChild(createHraRow("2024-01", "2026-12", "10.0"));
        }
    });

    // Populate Default preset
    hraPresets.value = "corrected";
    hraPresets.dispatchEvent(new Event("change"));

    // Collect HRA rates list
    function getHraRatesData() {
        const rows = hraTableBody.querySelectorAll("tr");
        const list = [];
        rows.forEach(tr => {
            const from = tr.querySelector(".hra-from").value.trim();
            const to = tr.querySelector(".hra-to").value.trim();
            const rate = parseFloat(tr.querySelector(".hra-rate").value.trim());
            if (from && to && !isNaN(rate)) {
                list.push({
                    from_month: from,
                    to_month: to,
                    rate_percent: rate
                });
            }
        });
        return list;
    }



    // Submit handler (Generate Excel and download)
    arrearForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const schoolName = document.getElementById("school-name").value.trim();
        const blockName = document.getElementById("block-name").value.trim();
        const designation = document.getElementById("designation") ? document.getElementById("designation").value.trim() : "";
        const joiningBasic = document.getElementById("joining-basic") ? document.getElementById("joining-basic").value.trim() : "";
        const scopeStart = document.getElementById("scope-start") ? document.getElementById("scope-start").value : "";
        const scopeEnd = document.getElementById("scope-end") ? document.getElementById("scope-end").value : "";
        
        if (!schoolName || !blockName) {
            alert("Please enter School Name and Block Name.");
            return;
        }

        const formData = new FormData();
        Object.keys(files).forEach(key => {
            formData.append(key, files[key]);
        });
        
        formData.append("school_name", schoolName);
        formData.append("block_name", blockName);
        formData.append("designation", designation);
        formData.append("joining_basic", joiningBasic);
        formData.append("scope_start", scopeStart);
        formData.append("scope_end", scopeEnd);
        
        const hraData = getHraRatesData();
        formData.append("hra_rates", JSON.stringify(hraData));
        formData.append("da_rates", JSON.stringify(getDaRatesData()));
        
        const typeEl = document.querySelector('input[name="arrear_type"]:checked');
        formData.append("arrear_type", typeEl ? typeEl.value : "both");
        
        btnSubmit.textContent = "📥 Generating Excel...";
        btnSubmit.disabled = true;
        startProgressBar("Uploading documents for spreadsheet generation...");

        try {
            const response = await fetch(`${API_BASE_URL}/api/generate-arrear`, {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Generation failed");
            }

            // Get content disposition filename if available
            let filename = "DPO_Arrear_Form.xlsx";
            const disposition = response.headers.get("content-disposition");
            if (disposition && disposition.indexOf("filename=") !== -1) {
                const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
                if (matches != null && matches[1]) { 
                    filename = matches[1].replace(/['"]/g, '');
                }
            }

            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = downloadUrl;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(downloadUrl);
            finishProgressBar("Excel file generated successfully! Downloading...");
            
            // Trigger donation modal
            setTimeout(() => {
                const modal = document.getElementById("donation-modal");
                if (modal) {
                    modal.style.display = "flex";
                }
            }, 1000);
        } catch (err) {
            failProgressBar("Generation failed: " + err.message);
            alert("Error: " + err.message);
        } finally {
            btnSubmit.textContent = "📥 Generate & Download";
            btnSubmit.disabled = false;
        }
    });

    // Donation Modal Handlers
    const donationModal = document.getElementById("donation-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const btnModalOk = document.getElementById("btn-modal-ok");

    if (btnCloseModal && donationModal) {
        btnCloseModal.addEventListener("click", () => {
            donationModal.style.display = "none";
        });
    }

    if (btnModalOk && donationModal) {
        btnModalOk.addEventListener("click", () => {
            donationModal.style.display = "none";
        });
    }

    if (donationModal) {
        donationModal.addEventListener("click", (e) => {
            if (e.target === donationModal) {
                donationModal.style.display = "none";
            }
        });
    }
});
