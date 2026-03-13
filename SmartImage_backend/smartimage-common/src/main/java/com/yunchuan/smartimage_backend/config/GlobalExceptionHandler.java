package com.yunchuan.smartimage_backend.config;

import com.yunchuan.smartimage_backend.common.ApiResponse;
import com.yunchuan.smartimage_backend.common.BusinessException;
import jakarta.validation.ConstraintViolationException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.multipart.MultipartException;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(BusinessException.class)
    public ApiResponse<Void> handleBusiness(BusinessException ex) {
        return ApiResponse.failure(ex.getCode(), ex.getMessage());
    }

    @ExceptionHandler({MethodArgumentNotValidException.class, ConstraintViolationException.class, IllegalArgumentException.class})
    public ApiResponse<Void> handleValidation(Exception ex) {
        String message = ex.getMessage();
        if (ex instanceof MethodArgumentNotValidException manv && manv.getBindingResult().getFieldError() != null) {
            message = manv.getBindingResult().getFieldError().getDefaultMessage();
        }
        return ApiResponse.failure(400, message);
    }

    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public ApiResponse<Void> handleMaxUploadSize(MaxUploadSizeExceededException ex) {
        return ApiResponse.failure(413, "upload file too large, compress it or send a download link");
    }

    @ExceptionHandler(MultipartException.class)
    public ApiResponse<Void> handleMultipartException(MultipartException ex) {
        String message = ex.getMessage() == null ? "" : ex.getMessage();
        Throwable cause = ex.getCause();
        if (cause != null && cause.getMessage() != null) {
            message = message + " " + cause.getMessage();
        }
        String lower = message.toLowerCase();
        if (lower.contains("maximum upload size exceeded") || lower.contains("size exceeded")) {
            return ApiResponse.failure(413, "upload file too large, compress it or send a download link");
        }
        return ApiResponse.failure(400, "upload failed, please retry");
    }

    @ExceptionHandler(Exception.class)
    public ApiResponse<Void> handleOther(Exception ex) {
        String message = ex.getMessage() == null ? "" : ex.getMessage();
        String lower = message.toLowerCase();
        if (lower.contains("maximum upload size exceeded") || lower.contains("size exceeded")) {
            return ApiResponse.failure(413, "upload file too large, compress it or send a download link");
        }
        return ApiResponse.failure(500, "message" + ex.getMessage());
    }
}
