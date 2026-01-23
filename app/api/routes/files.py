"""File serving API endpoints."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
from urllib.parse import unquote
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


def get_files_base_dir():
    """Get files directory with fallbacks for different deployment scenarios."""
    # Try relative to this file (development)
    base = Path(__file__).parent.parent.parent.parent / "files"
    if base.exists():
        logger.info(f"Using development files directory: {base}")
        return base
    
    # Try relative to current working directory (production)
    base = Path.cwd() / "files"
    if base.exists():
        logger.info(f"Using production files directory (cwd): {base}")
        return base
    
    # Try absolute path from environment variable
    if os.getenv("FILES_DIR"):
        base = Path(os.getenv("FILES_DIR"))
        if base.exists():
            logger.info(f"Using files directory from environment: {base}")
            return base
    
    # Default fallback (may not exist, but we'll use it for error messages)
    default_base = Path(__file__).parent.parent.parent.parent / "files"
    logger.warning(f"Files directory not found, using default: {default_base}")
    return default_base


# Base directory for files (with fallbacks for production)
FILES_BASE_DIR = get_files_base_dir()


@router.get("/health")
async def file_health_check():
    """
    Check if file directory is accessible and list available files.
    
    This endpoint helps diagnose file serving issues by showing:
    - Whether the files directory exists
    - What files are available
    - Directory path being used
    """
    try:
        logger.info("File health check requested")
        
        if not FILES_BASE_DIR.exists():
            logger.error(f"Files directory does not exist: {FILES_BASE_DIR}")
            return {
                "status": "error",
                "message": f"Files directory does not exist: {FILES_BASE_DIR}",
                "path": str(FILES_BASE_DIR),
                "current_working_directory": str(Path.cwd()),
                "script_location": str(Path(__file__).parent)
            }
        
        # List all files in directory
        all_items = list(FILES_BASE_DIR.glob("*"))
        files = [f for f in all_items if f.is_file()]
        directories = [d for d in all_items if d.is_dir()]
        
        # Categorize files by type
        step_files = [f.name for f in files if f.suffix.lower() in ['.step', '.stp']]
        pdf_files = [f.name for f in files if f.suffix.lower() == '.pdf']
        dwg_files = [f.name for f in files if f.suffix.lower() in ['.dwg', '.dxf']]
        other_files = [f.name for f in files if f.suffix.lower() not in ['.step', '.stp', '.pdf', '.dwg', '.dxf']]
        
        logger.info(f"Health check: Found {len(files)} files in {FILES_BASE_DIR}")
        
        return {
            "status": "ok",
            "directory": str(FILES_BASE_DIR),
            "directory_exists": True,
            "total_files": len(files),
            "total_directories": len(directories),
            "step_files": step_files,
            "pdf_files": pdf_files,
            "dwg_files": dwg_files,
            "other_files": other_files,
            "all_files": [f.name for f in files],
            "directories": [d.name for d in directories],
            "current_working_directory": str(Path.cwd())
        }
    except Exception as e:
        logger.error(f"Error in file health check: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "path": str(FILES_BASE_DIR),
            "current_working_directory": str(Path.cwd())
        }


@router.get("/{filename}")
async def get_file(filename: str):
    """
    Serve a file by filename.
    
    Looks for files in the files/ directory. Supports both drawing files
    (PDF, DWG) and step files (.step, .STEP).
    
    Args:
        filename: Name of the file to retrieve (e.g., "drawing_PR001_main.pdf" or "model_PR001.step")
    
    Returns:
        FileResponse with the file content
    
    Raises:
        HTTPException 404 if file not found
    """
    try:
        # Decode URL-encoded filename (handles %20, %2E, etc.)
        original_filename = filename
        filename = unquote(filename)
        
        if original_filename != filename:
            logger.info(f"Decoded filename: '{original_filename}' -> '{filename}'")
        
        logger.info(f"Requesting file: {filename}")
        logger.info(f"Looking in directory: {FILES_BASE_DIR}")
        
        # Security: Prevent directory traversal attacks (check after decoding)
        if ".." in filename or "/" in filename or "\\" in filename:
            logger.warning(f"Invalid filename (directory traversal attempt): {filename}")
            raise HTTPException(
                status_code=400,
                detail="Invalid filename"
            )
        
        # Construct file path
        file_path = FILES_BASE_DIR / filename
        logger.info(f"Full file path: {file_path}")
        
        # Check if files directory exists
        if not FILES_BASE_DIR.exists():
            logger.error(f"Files directory does not exist: {FILES_BASE_DIR}")
            raise HTTPException(
                status_code=500,
                detail=f"Files directory not found: {FILES_BASE_DIR}"
            )
        
        # Check if file exists
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            
            # List available files for debugging
            try:
                available_files = [f.name for f in FILES_BASE_DIR.glob("*") if f.is_file()]
                logger.error(f"Available files in directory: {available_files}")
                
                # Provide helpful error message
                error_detail = f"File '{filename}' not found in {FILES_BASE_DIR}"
                if available_files:
                    error_detail += f". Available files: {', '.join(available_files[:10])}"
                    if len(available_files) > 10:
                        error_detail += f" (and {len(available_files) - 10} more)"
            except Exception as list_error:
                logger.error(f"Error listing files: {list_error}")
                error_detail = f"File '{filename}' not found in {FILES_BASE_DIR}"
            
            raise HTTPException(
                status_code=404,
                detail=error_detail
            )
        
        logger.info(f"File found, serving: {file_path}")
        
        # Determine media type based on file extension
        media_type = None
        filename_lower = filename.lower()
        if filename_lower.endswith('.pdf'):
            media_type = 'application/pdf'
        elif filename_lower.endswith(('.dwg', '.dxf')):
            media_type = 'application/acad'
        elif filename_lower.endswith('.step') or filename_lower.endswith('.stp'):
            media_type = 'application/octet-stream'  # STEP files are binary
        
        if not media_type:
            media_type = 'application/octet-stream'  # Default for unknown types
        
        logger.info(f"Serving file with content-type: {media_type}")
        
        return FileResponse(
            path=str(file_path),
            media_type=media_type,
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error retrieving file '{filename}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving file: {str(e)}"
        )


@router.get("/rfq/{rfq_id}/{filename}")
async def get_rfq_file(rfq_id: str, filename: str):
    """
    Serve a file associated with a specific RFQ.
    
    This endpoint allows serving files in an RFQ-specific context.
    Currently serves from the same files directory but could be extended
    to organize files by RFQ ID.
    
    Args:
        rfq_id: RFQ identifier
        filename: Name of the file to retrieve
    
    Returns:
        FileResponse with the file content
    """
    logger.info(f"RFQ-specific file request: RFQ {rfq_id}, file {filename}")
    # For now, just use the regular file endpoint logic
    # In the future, this could organize files by RFQ: files/rfq/{rfq_id}/{filename}
    return await get_file(filename)
