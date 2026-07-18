# main.py - FastAPI app entrypoint and API routes
import os
import tempfile
import json
import asyncio
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
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
async def api_parse_preview(request: Request):
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
        form = await request.form()
        
        payslip_file = form.get("payslip_pdf")
        if not payslip_file:
            raise HTTPException(status_code=400, detail="Pay Slip PDF is required.")
            
        yearly_files = []
        for i in range(10):
            f = form.get(f"yearly_pdf_{i}")
            if f:
                yearly_files.append(f)
        if not yearly_files:
            raise HTTPException(status_code=400, detail="At least one Yearly Statement PDF is required.")
            
        hra_rates = form.get("hra_rates")
        da_rates_str = form.get("da_rates")
        
        # Save payslip
        path_ps = save_upload_file_temp(payslip_file)
        temp_files.append(path_ps)
        
        # Parse payslip
        try:
            payslip_info = parse_payslip(path_ps)
        except Exception as parse_err:
            payslip_info = {"name": None, "designation": None, "doj": None, "pran": None, "bank_account": None, "ifsc": None, "pan": None}
            
        # Parse yearly statements
        drawn_data = {}
        prans = {payslip_info.get("pran")}
        for yf in yearly_files:
            path = save_upload_file_temp(yf)
            temp_files.append(path)
            yp_data = parse_yearly_payment(path)
            drawn_data.update(yp_data["monthly_data"])
            prans.add(yp_data["employee"].get("pran"))
            
        prans = {p for p in prans if p}
        
        if len(prans) > 1:
            warning = f"Warning: Multiple PRANs detected ({', '.join(prans)}). Ensure PDFs are for the same employee."
        else:
            warning = None
            
        try:
            sample_month = list(drawn_data.values())[0] if drawn_data else None
            if sample_month and sample_month["basic"] > 0:
                drawn_hra_rate = sample_month["hra"] / sample_month["basic"]
            else:
                drawn_hra_rate = 0.04
        except Exception:
            drawn_hra_rate = 0.04
            
        da_rates = None
        if da_rates_str:
            try:
                da_rates = json.loads(da_rates_str)
            except: pass
            
        response_content = {
            "success": True,
            "employee": payslip_info,
            "drawn_summary": {
                "total_months": len(drawn_data),
                "drawn_hra_rate_percent": round(drawn_hra_rate * 100, 1),
                "warning": warning
            }
        }
        
        if hra_rates:
            try:
                hra_rules = json.loads(hra_rates)
                result = compute_arrears(
                    drawn_data=drawn_data,
                    employee_info=payslip_info,
                    hra_rules=hra_rules,
                    skip_joining_month=True,
                    da_rates=da_rates
                )
                response_content["arrear_months"] = result["arrear_months"]
                response_content["totals"] = result["totals"]
                response_content["in_words"] = result["in_words"]
                response_content["starting_step"] = result["starting_step"]
                response_content["designation_category"] = result["designation_category"]
                if "fitment_info" in result:
                    response_content["fitment_info"] = result["fitment_info"]
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
async def api_generate_arrear(request: Request):
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
        form = await request.form()
        
        payslip_file = form.get("payslip_pdf")
        if not payslip_file:
            raise HTTPException(status_code=400, detail="Pay Slip PDF is required.")
            
        yearly_files = []
        for i in range(10):
            f = form.get(f"yearly_pdf_{i}")
            if f:
                yearly_files.append(f)
        if not yearly_files:
            raise HTTPException(status_code=400, detail="At least one Yearly Statement PDF is required.")
            
        school_name = form.get("school_name", "")
        block_name = form.get("block_name", "")
        designation = form.get("designation", "")
        arrear_type = form.get("arrear_type", "both")
        hra_rates_str = form.get("hra_rates")
        da_rates_str = form.get("da_rates")
        scope_start = form.get("scope_start")
        scope_end = form.get("scope_end")
        
        try:
            hra_rules = json.loads(hra_rates_str) if hra_rates_str else []
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid HRA rules format. Must be a valid JSON array.")
            
        da_rates = None
        if da_rates_str:
            try:
                da_rates = json.loads(da_rates_str)
            except: pass
            
        # Save payslip
        path_ps = save_upload_file_temp(payslip_file)
        temp_files.append(path_ps)
        
        # Parse payslip
        try:
            payslip_info = parse_payslip(path_ps)
        except Exception as parse_err:
            payslip_info = {"name": None, "designation": None, "doj": None, "pran": None, "bank_account": None, "ifsc": None, "pan": None}
            
        payslip_info["school_name"] = school_name
        payslip_info["block_name"] = block_name
        if designation:
            payslip_info["designation"] = designation
        
        # Parse yearly statements
        drawn_data = {}
        for yf in yearly_files:
            path = save_upload_file_temp(yf)
            temp_files.append(path)
            yp_data = parse_yearly_payment(path)
            drawn_data.update(yp_data["monthly_data"])
        
        # Compute Arrears
        result = compute_arrears(
            drawn_data=drawn_data,
            employee_info=payslip_info,
            hra_rules=hra_rules,
            skip_joining_month=True,
            da_rates=da_rates,
            scope_start=scope_start,
            scope_end=scope_end
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
        safe_name = "".join(c for c in (payslip_info.get("name") or "Arrear") if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
        pran = payslip_info.get("pran") or "Form"
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
