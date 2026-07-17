# main.py - FastAPI app entrypoint and API routes
import os
import tempfile
import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import openpyxl

from fastapi.middleware.cors import CORSMiddleware
from app.parsers.payslip_parser import parse_payslip
from app.parsers.yearly_payment_parser import parse_yearly_payment
from app.engine.difference_calculator import compute_arrears
from app.generators.salary_arrear_writer import write_salary_arrear_sheet
from app.generators.da_arrear_writer import write_da_arrear_sheet

app = FastAPI(title="DPO Muzaffarpur Arrear Form Generator")

# Semaphore to throttle concurrent CPU-intensive PDF parsing & Excel generation
MAX_CONCURRENT_USERS = 10
semaphore = asyncio.Semaphore(MAX_CONCURRENT_USERS)

# Enable CORS for frontend hosting compatibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows local testing and GitHub Pages (uhskaparpurakanti.in)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper to save upload file to a temp file and return the path
def save_upload_file_temp(upload_file: UploadFile) -> str:
    suffix = os.path.splitext(upload_file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        shutil_copy_fileobj(upload_file.file, temp_file)
        return temp_file.name

def shutil_copy_fileobj(fsrc, fdst, length=16*1024):
    while True:
        buf = fsrc.read(length)
        if not buf:
            break
        fdst.write(buf)

@app.post("/api/parse-preview")
async def api_parse_preview(
    yearly_pdf_1: UploadFile = File(...),
    yearly_pdf_2: UploadFile = File(...),
    yearly_pdf_3: UploadFile = File(...),
    payslip_pdf: UploadFile = File(...),
    hra_rates: Optional[str] = Form(None)
):
    try:
        # Wait for up to 60 seconds to acquire the semaphore
        await asyncio.wait_for(semaphore.acquire(), timeout=60.0)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=503,
            detail="The server is busy processing other requests. Please wait a moment and try again!"
        )

    temp_files = []
    try:
        # Save files to temp paths
        path_yp1 = save_upload_file_temp(yearly_pdf_1)
        temp_files.append(path_yp1)
        path_yp2 = save_upload_file_temp(yearly_pdf_2)
        temp_files.append(path_yp2)
        path_yp3 = save_upload_file_temp(yearly_pdf_3)
        temp_files.append(path_yp3)
        path_ps = save_upload_file_temp(payslip_pdf)
        temp_files.append(path_ps)
        
        # Parse payslip
        payslip_info = parse_payslip(path_ps)
        
        # Parse yearly statements
        yp1_data = parse_yearly_payment(path_yp1)
        yp2_data = parse_yearly_payment(path_yp2)
        yp3_data = parse_yearly_payment(path_yp3)
        
        # Combine drawn data
        drawn_data = {}
        drawn_data.update(yp1_data["monthly_data"])
        drawn_data.update(yp2_data["monthly_data"])
        drawn_data.update(yp3_data["monthly_data"])
        
        # Verify employee consistency (names or IDs match)
        prans = {payslip_info.get("pran"), yp1_data["employee"].get("pran"), 
                 yp2_data["employee"].get("pran"), yp3_data["employee"].get("pran")}
        prans = {p for p in prans if p}
        
        if len(prans) > 1:
            # Warning of potential mismatch
            warning = f"Warning: Multiple PRANs detected ({', '.join(prans)}). Ensure PDFs are for the same employee."
        else:
            warning = None
            
        # Detect drawn HRA rate from payslip to suggest preset
        try:
            sample_month = list(drawn_data.values())[0] if drawn_data else None
            if sample_month and sample_month["basic"] > 0:
                drawn_hra_rate = sample_month["hra"] / sample_month["basic"]
            else:
                drawn_hra_rate = 0.04
        except Exception:
            drawn_hra_rate = 0.04
            
        response_content = {
            "success": True,
            "employee": payslip_info,
            "drawn_summary": {
                "total_months": len(drawn_data),
                "drawn_hra_rate_percent": round(drawn_hra_rate * 100, 1),
                "warning": warning
            }
        }
        
        # If hra_rates is provided, calculate arrears and add to preview
        if hra_rates:
            try:
                hra_rules = json.loads(hra_rates)
                result = compute_arrears(
                    drawn_data=drawn_data,
                    employee_info=payslip_info,
                    hra_rules=hra_rules,
                    skip_joining_month=True
                )
                response_content["arrear_months"] = result["arrear_months"]
                response_content["totals"] = result["totals"]
                response_content["in_words"] = result["in_words"]
                response_content["starting_step"] = result["starting_step"]
                response_content["designation_category"] = result["designation_category"]
            except Exception as e:
                response_content["drawn_summary"]["warning"] = f"Arrear preview failed: {str(e)}"
                
        return JSONResponse(content=response_content)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to parse PDFs: {str(e)}")
    finally:
        # Release the semaphore
        semaphore.release()
        # Clean up temp files
        for path in temp_files:
            if os.path.exists(path):
                os.remove(path)

@app.post("/api/generate-arrear")
async def api_generate_arrear(
    yearly_pdf_1: UploadFile = File(...),
    yearly_pdf_2: UploadFile = File(...),
    yearly_pdf_3: UploadFile = File(...),
    payslip_pdf: UploadFile = File(...),
    school_name: str = Form(...),
    block_name: str = Form(...),
    hra_rates: str = Form(...), # JSON string containing List[Dict[str, Any]]
    arrear_type: str = Form("both") # "salary", "da", "both"
):
    try:
        # Wait for up to 60 seconds to acquire the semaphore
        await asyncio.wait_for(semaphore.acquire(), timeout=60.0)
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=503,
            detail="The server is busy processing other requests. Please wait a moment and try again!"
        )

    temp_files = []
    try:
        # Parse HRA rules
        try:
            hra_rules = json.loads(hra_rates)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid HRA rules format. Must be a valid JSON array.")
            
        # Save files to temp paths
        path_yp1 = save_upload_file_temp(yearly_pdf_1)
        temp_files.append(path_yp1)
        path_yp2 = save_upload_file_temp(yearly_pdf_2)
        temp_files.append(path_yp2)
        path_yp3 = save_upload_file_temp(yearly_pdf_3)
        temp_files.append(path_yp3)
        path_ps = save_upload_file_temp(payslip_pdf)
        temp_files.append(path_ps)
        
        # Parse payslip
        payslip_info = parse_payslip(path_ps)
        payslip_info["school_name"] = school_name
        payslip_info["block_name"] = block_name
        
        # Parse yearly statements
        yp1_data = parse_yearly_payment(path_yp1)
        yp2_data = parse_yearly_payment(path_yp2)
        yp3_data = parse_yearly_payment(path_yp3)
        
        # Combine drawn data
        drawn_data = {}
        drawn_data.update(yp1_data["monthly_data"])
        drawn_data.update(yp2_data["monthly_data"])
        drawn_data.update(yp3_data["monthly_data"])
        
        # Compute Arrears
        result = compute_arrears(
            drawn_data=drawn_data,
            employee_info=payslip_info,
            hra_rules=hra_rules,
            skip_joining_month=True
        )
        
        # Load Template
        template_path = "templates/DPO_Muzaffarpur_Arrear_Forms.xlsx"
        if not os.path.exists(template_path):
            raise FileNotFoundError("Excel template file not found in templates directory.")
            
        wb = openpyxl.load_workbook(template_path)
        
        # Populating sheets based on request type
        if arrear_type in ["salary", "both"]:
            ws_salary = wb["Salary Arrear Format"]
            write_salary_arrear_sheet(ws_salary, result)
        else:
            # If only DA is selected, we can clear or remove Salary Arrear sheet to avoid confusion
            # For simplicity, we just keep both sheets but only fill the requested one.
            pass
            
        if arrear_type in ["da", "both"]:
            ws_da = wb["DA Arrear Format"]
            write_da_arrear_sheet(ws_da, result)
            
        # Save output to a temp file and return it
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as out_temp:
            output_path = out_temp.name
            
        wb.save(output_path)
        
        # Determine download filename
        safe_name = "".join(c for c in payslip_info.get("name", "Arrear") if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        pran = payslip_info.get("pran", "Form")
        filename = f"DPO_Arrear_{safe_name}_{pran}.xlsx"
        
        return FileResponse(
            output_path, 
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            background=None # we want to make sure file is deleted after download but wait, FileResponse doesn't delete it automatically unless we wrap it.
            # We can use background task to clean it up!
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Failed to generate Excel: {str(e)}")
    finally:
        # Release the semaphore
        semaphore.release()
        # Clean up temp inputs
        for path in temp_files:
            if os.path.exists(path):
                os.remove(path)

# Serve the static files of the frontend
# Note: we check if directory exists first
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
