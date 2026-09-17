# template_manager.py - Loading, cloning, and formatting the Excel templates
import openpyxl
from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
from openpyxl.worksheet.cell_range import CellRange
from openpyxl.worksheet.page import PrintPageSetup, PageMargins
from openpyxl.utils import get_column_letter
from copy import copy
import shutil
import os

def copy_cell_style(src_cell, dest_cell):
    """
    Copies style (font, alignment, border, fill, number_format) from src_cell to dest_cell.
    """
    if src_cell.has_style:
        dest_cell.font = copy(src_cell.font)
        dest_cell.alignment = copy(src_cell.alignment)
        dest_cell.border = copy(src_cell.border)
        dest_cell.fill = copy(src_cell.fill)
        dest_cell.number_format = copy(src_cell.number_format)

def adjust_rows_in_sheet(ws, required_rows, first_data_row=8, total_row_label_cell="A21"):
    """
    Adjusts the number of rows in the table.
    - If required_rows > available placeholder rows (20 - 8 + 1 = 13), inserts rows before the G.TOTAL row.
    - If required_rows < 13, deletes unused placeholder rows so that the layout is clean.
    - Copies styling from the first_data_row to all new rows.
    - Manually shifts merged cell ranges to prevent openpyxl corrupting them.
    """
    placeholder_rows = 13 # rows 8 to 20
    diff = required_rows - placeholder_rows
    
    # Identify the current total row index
    total_row_idx = 21
    for r in range(first_data_row, ws.max_row + 1):
        if ws.cell(row=r, column=1).value == "G.TOTAL":
            total_row_idx = r
            break
            
    if diff > 0:
        # Shift merged cell ranges manually before inserting rows
        merged_ranges = list(ws.merged_cells.ranges)
        for r_range in merged_ranges:
            if r_range.min_row >= total_row_idx:
                ws.merged_cells.remove(r_range)
                r_range.shift(row_shift=diff)
                ws.merged_cells.add(r_range)
                
        # Insert rows right before the total row
        ws.insert_rows(total_row_idx, diff)
        # Copy styles from the first data row (row 8) to the newly inserted rows
        for r in range(total_row_idx, total_row_idx + diff):
            for c in range(1, ws.max_column + 1):
                src_cell = ws.cell(row=first_data_row, column=c)
                dest_cell = ws.cell(row=r, column=c)
                copy_cell_style(src_cell, dest_cell)
    elif diff < 0:
        # Delete unused rows right before the total row
        rows_to_delete = -diff
        start_delete_row = total_row_idx - rows_to_delete
        
        # Shift merged ranges UP (diff is negative)
        merged_ranges = list(ws.merged_cells.ranges)
        for r_range in merged_ranges:
            if r_range.min_row >= total_row_idx:
                ws.merged_cells.remove(r_range)
                r_range.shift(row_shift=diff)
                ws.merged_cells.add(r_range)
                
        ws.delete_rows(start_delete_row, rows_to_delete)
        
    # Return the new total row index
    for r in range(first_data_row, ws.max_row + 1):
        if ws.cell(row=r, column=1).value == "G.TOTAL":
            return r
    return 21

def format_total_row_formulas(ws, total_row_idx, start_row=8, cols_range=None):
    """
    Adds SUM formulas to the total row cells for the specified columns.
    E.g. =SUM(C8:C20)
    """
    if not cols_range:
        return
        
    for col_let in cols_range:
        cell = ws[f"{col_let}{total_row_idx}"]
        cell.value = f"=SUM({col_let}{start_row}:{col_let}{total_row_idx-1})"
        
        # Ensure it is bold
        cell.font = Font(name=cell.font.name, size=cell.font.size, bold=True)


def configure_print_layout(ws, last_col_letter, last_row, header_rows=7, data_row_height=18.0):
    """
    Configures the worksheet for single-page print layout so teachers
    can print directly without needing to adjust any settings.
    
    Args:
        ws: The openpyxl worksheet object.
        last_col_letter: The last column letter (e.g., 'Z' for Salary, 'Q' for DA).
        last_row: The last row to include in the print area (typically sig_row).
        header_rows: Number of header rows (rows 1-7 have different formatting).
        data_row_height: Uniform height for data rows (in points).
    """
    # --- 1. Page Setup: Fit to one page, landscape ---
    ws.page_setup.orientation = 'landscape'
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    
    # --- 2. Narrow Margins (inches) for maximum content area ---
    ws.page_margins = PageMargins(
        left=0.25,
        right=0.25,
        top=0.4,
        bottom=0.4,
        header=0.2,
        footer=0.2
    )
    
    # --- 3. Print Area ---
    ws.print_area = f'A1:{last_col_letter}{last_row}'
    
    # --- 4. Center content on page ---
    ws.print_options.horizontalCentered = True
    ws.print_options.verticalCentered = False
    
    # --- 5. Uniform Column Widths ---
    # Calculate total columns from the last_col_letter
    from openpyxl.utils import column_index_from_string
    total_cols = column_index_from_string(last_col_letter)
    
    # Column A (Month/Serial) gets slightly more width; rest are uniform
    col_a_width = 12.0
    # For A4 Landscape with narrow margins, usable width ~35cm ≈ ~130 Excel units
    # Distribute remaining width evenly across data columns
    remaining_width = max(8.0, (130.0 - col_a_width) / max(1, total_cols - 1))
    # Cap at reasonable maximum for readability
    uniform_width = min(remaining_width, 12.0)
    
    ws.column_dimensions['A'].width = col_a_width
    for col_idx in range(2, total_cols + 1):
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = uniform_width
    
    # --- 6. Uniform Row Heights ---
    # Header rows (1-7) keep their existing heights or get a reasonable default
    for row in range(1, header_rows + 1):
        if ws.row_dimensions[row].height is None:
            ws.row_dimensions[row].height = 20.0
    
    # Data rows + total row get uniform height
    for row in range(header_rows + 1, last_row + 1):
        ws.row_dimensions[row].height = data_row_height
