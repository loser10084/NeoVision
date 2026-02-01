package com.yunchuan.smartimage_backend.controller;

import com.yunchuan.smartimage_backend.common.ApiResponse;
import com.yunchuan.smartimage_backend.service.FileService;
import com.yunchuan.smartimage_backend.vo.FileVO;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/files")
public class FileController {

    private final FileService fileService;

    public FileController(FileService fileService) {
        this.fileService = fileService;
    }

    @GetMapping("/{fileId}")
    public ApiResponse<FileVO> getFile(@PathVariable("fileId") Long fileId) {
        return ApiResponse.success(fileService.find(fileId));
    }

    @DeleteMapping("/{fileId}")
    public ApiResponse<Void> deleteFile(@PathVariable("fileId") Long fileId) {
        fileService.delete(fileId);
        return ApiResponse.success(null);
    }
}
