// script.js - Client side logic, drag & drop, dynamic HRA rows, and API requests

window.onerror = function(message, source, lineno, colno, error) {
    alert("JS Debug Error: " + message + "\nLine: " + lineno + "\nSource: " + source);
    return false;
};

document.addEventListener("DOMContentLoaded", () => {
    // Determine API Base URL depending on local testing vs production domain
    const API_BASE_URL = window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost"
        ? ""
        : "https://arrear-api.uhskaparpurakanti.in";

    // Files tracking object
    const files = {
        yearly_pdf_1: null,
        yearly_pdf_2: null,
        yearly_pdf_3: null,
        payslip_pdf: null
    };

    // DOM Elements
    const dropZones = {
        yearly_pdf_1: document.getElementById("dz-yp1"),
        yearly_pdf_2: document.getElementById("dz-yp2"),
        yearly_pdf_3: document.getElementById("dz-yp3"),
        payslip_pdf: document.getElementById("dz-ps")
    };

    const fileInputs = {
        yearly_pdf_1: document.getElementById("file-yp1"),
        yearly_pdf_2: document.getElementById("file-yp2"),
        yearly_pdf_3: document.getElementById("file-yp3"),
        payslip_pdf: document.getElementById("file-ps")
    };

    const badges = {
        yearly_pdf_1: document.getElementById("name-yp1"),
        yearly_pdf_2: document.getElementById("name-yp2"),
        yearly_pdf_3: document.getElementById("name-yp3"),
        payslip_pdf: document.getElementById("name-ps")
    };

    const btnPreview = document.getElementById("btn-preview");
    const btnSubmit = document.getElementById("btn-submit");
    const btnAddHra = document.getElementById("btn-add-hra");
    const hraPresets = document.getElementById("hra-presets");
    const hraTableBody = document.getElementById("hra-table-body");
    const arrearForm = document.getElementById("arrear-form");

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

    // Initialize Drop Zones
    Object.keys(dropZones).forEach(key => {
        const zone = dropZones[key];
        const input = fileInputs[key];
        const badge = badges[key];

        // Click to open file browser (stopping propagation on input to prevent infinite bubbling loop)
        input.addEventListener("click", (e) => e.stopPropagation());
        zone.addEventListener("click", () => input.click());

        // File selection handler
        input.addEventListener("change", (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(key, e.target.files[0], badge);
            }
        });

        // Drag & Drop handlers
        zone.addEventListener("dragover", (e) => {
            e.preventDefault();
            zone.classList.add("dragover");
        });

        zone.addEventListener("dragleave", () => {
            zone.classList.remove("dragover");
        });

        zone.addEventListener("drop", (e) => {
            e.preventDefault();
            zone.classList.remove("dragover");
            if (e.dataTransfer.files.length > 0) {
                input.files = e.dataTransfer.files; // assign to input
                handleFileSelect(key, e.dataTransfer.files[0], badge);
            }
        });
    });

    function handleFileSelect(key, file, badge) {
        if (file.type !== "application/pdf") {
            alert("Please upload a PDF file.");
            return;
        }
        files[key] = file;
        badge.textContent = file.name;
        badge.style.display = "block";
        checkFilesReady();
    }

    function checkFilesReady() {
        const allUploaded = Object.values(files).every(file => file !== null);
        btnPreview.disabled = !allUploaded;
        btnSubmit.disabled = !allUploaded;
    }

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

    // Preview click handler
    btnPreview.addEventListener("click", async () => {
        const formData = new FormData();
        Object.keys(files).forEach(key => {
            formData.append(key, files[key]);
        });
        
        const hraData = getHraRatesData();
        formData.append("hra_rates", JSON.stringify(hraData));
        
        btnPreview.textContent = "🔄 Parsing...";
        btnPreview.disabled = true;

        try {
            const response = await fetch(`${API_BASE_URL}/api/parse-preview`, {
                method: "POST",
                body: formData
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "Parse failed");
            }

            const data = await response.json();
            renderPreview(data);
        } catch (err) {
            alert("Error: " + err.message);
        } finally {
            btnPreview.textContent = "🔄 Parse & Preview";
            btnPreview.disabled = false;
        }
    });

    function renderPreview(data) {
        previewPlaceholder.style.display = "none";
        previewContent.style.display = "block";
        
        const emp = data.employee;
        previewName.textContent = emp.name || "Unknown";
        previewDesig.textContent = emp.designation || "Unknown";
        
        if (data.designation_category && data.starting_step) {
            previewStep.textContent = `Step ${data.starting_step} (${data.designation_category})`;
            previewStep.style.display = "block";
        } else {
            previewStep.style.display = "none";
        }
        
        previewDoj.textContent = emp.doj || "N/A";
        previewPran.textContent = emp.pran || "N/A";
        previewPan.textContent = emp.pan || "N/A";
        
        // Determine increment month
        if (emp.doj) {
            const parts = emp.doj.split("-");
            if (parts.length >= 2) {
                const month = parseInt(parts[1]);
                previewIncMonth.textContent = (month >= 7 && month <= 12) ? "July" : "January";
            } else {
                previewIncMonth.textContent = "N/A";
            }
        } else {
            previewIncMonth.textContent = "N/A";
        }
        
        // Warning notification
        const summaryInfo = data.drawn_summary;
        if (summaryInfo.warning) {
            warningBox.textContent = summaryInfo.warning;
            warningBox.style.display = "block";
        } else {
            warningBox.style.display = "none";
        }

        // Totals metrics
        if (data.totals) {
            previewTotalArrear.textContent = `₹${data.totals.net.toLocaleString("en-IN")}`;
            previewInWords.textContent = data.in_words || "";
        } else {
            previewTotalArrear.textContent = "₹0";
            previewInWords.textContent = "Rupees Zero Only";
        }

        // Table details
        previewTableBody.innerHTML = "";
        if (data.arrear_months && data.arrear_months.length > 0) {
            data.arrear_months.forEach(item => {
                const tr = document.createElement("tr");
                const diff = item.difference;
                
                // Format values for cleaner look
                const basicDiff = diff.basic > 0 ? `+${diff.basic}` : `${diff.basic}`;
                const daDiff = diff.da > 0 ? `+${diff.da}` : `${diff.da}`;
                const hraDiff = diff.hra > 0 ? `+${diff.hra}` : `${diff.hra}`;
                const netDiff = diff.net > 0 ? `+${diff.net}` : `${diff.net}`;
                
                tr.innerHTML = `
                    <td><strong>${item.month_label}</strong></td>
                    <td>${item.admissible.days}</td>
                    <td class="${diff.basic > 0 ? 'text-success' : ''}">${basicDiff}</td>
                    <td class="${diff.da > 0 ? 'text-success' : ''}">${daDiff}</td>
                    <td class="${diff.hra > 0 ? 'text-success' : ''}">${hraDiff}</td>
                    <td class="text-bold ${diff.net > 0 ? 'text-success' : ''}">${netDiff}</td>
                `;
                previewTableBody.appendChild(tr);
            });
        } else {
            const tr = document.createElement("tr");
            tr.innerHTML = `<td colspan="6" style="text-align: center; color: var(--text-secondary);">No monthly differences detected. All drawn values match admissible.</td>`;
            previewTableBody.appendChild(tr);
        }
    }

    // Submit handler (Generate Excel and download)
    arrearForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const schoolName = document.getElementById("school-name").value.trim();
        const blockName = document.getElementById("block-name").value.trim();
        
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
        
        const hraData = getHraRatesData();
        formData.append("hra_rates", JSON.stringify(hraData));
        
        const typeEl = document.querySelector('input[name="arrear_type"]:checked');
        formData.append("arrear_type", typeEl ? typeEl.value : "both");
        
        btnSubmit.textContent = "📥 Generating Excel...";
        btnSubmit.disabled = true;

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
            
        } catch (err) {
            alert("Error: " + err.message);
        } finally {
            btnSubmit.textContent = "📥 Generate & Download";
            btnSubmit.disabled = false;
        }
    });
});
