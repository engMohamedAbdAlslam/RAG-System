from enum import Enum

class ResponseSignal(Enum):
    # file
    FILL_VALIDATED_SUCCESS = "file_validate_successfully"
    FILE_TYPE_NOT_SUPPORTED = "file_type_not_supported"
    FILE_SIZE_EXCEEDED = "file_size_exceeded"
    FILE_UPLOAD_SUCCESS = "file_upload_success"
    FILE_UPLOAD_FAILED = "file_upload_failed"
    NO_FILE_ERROES = "no_file_errors"
    FILE_NO_FOUND_ID ="no_file_found_id"

    # process
    PROCESSING_FAILD = "processing_filed"
    PROCESSING_SUCCESS = "processing_success"
    
    