package com.yunchuan.smartimage_backend.controller;

import com.yunchuan.smartimage_backend.common.ApiResponse;
import com.yunchuan.smartimage_backend.dto.FileUploadRequest;
import com.yunchuan.smartimage_backend.dto.StudyCreateRequest;
import com.yunchuan.smartimage_backend.dto.StudyUpdateRequest;
import com.yunchuan.smartimage_backend.entity.FileUpload;
import com.yunchuan.smartimage_backend.entity.PatientStudy;
import com.yunchuan.smartimage_backend.security.SecurityUtil;
import com.yunchuan.smartimage_backend.utils.AliOssUtil;
import com.yunchuan.smartimage_backend.service.FileService;
import com.yunchuan.smartimage_backend.service.StudyService;
import com.yunchuan.smartimage_backend.vo.StudyVO;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/patients")
public class StudyController {

    private final StudyService studyService;
    private final FileService fileService;
    private final AliOssUtil aliOssUtil;

    public StudyController(StudyService studyService, FileService fileService, AliOssUtil aliOssUtil) {
        this.studyService = studyService;
        this.fileService = fileService;
        this.aliOssUtil = aliOssUtil;
    }

    @GetMapping("/{patientId}/studies")
    public ApiResponse<List<StudyVO>> listStudies(@PathVariable("patientId") Long patientId) {
        return ApiResponse.success(studyService.list(patientId));
    }

    @PostMapping("/{patientId}/studies")
    public ApiResponse<Map<String, Object>> createStudy(@PathVariable("patientId") Long patientId,
                                                        @Valid @RequestBody StudyCreateRequest request) {
        PatientStudy study = studyService.create(patientId, request.getStudyUid(), request.getModality(), request.getDesc());
        Map<String, Object> result = new HashMap<>();
        result.put("id", study.getId());
        result.put("studyUid", study.getStudyUid());
        return ApiResponse.success(result);
    }

    @PutMapping("/{patientId}/studies/{studyId}")
    public ApiResponse<Void> updateStudy(@PathVariable("studyId") Long studyId, @RequestBody StudyUpdateRequest request) {
        studyService.update(studyId, request.getStudyUid(), request.getModality(), request.getDesc(), request.getStatus());
        return ApiResponse.success(null);
    }

    @DeleteMapping("/{patientId}/studies/{studyId}")
    public ApiResponse<Void> deleteStudy(@PathVariable("patientId") Long patientId,
                                         @PathVariable("studyId") Long studyId) {
        studyService.delete(patientId, studyId);
        return ApiResponse.success(null);
    }

    @PostMapping("/{patientId}/studies/{studyId}/upload")
    public ApiResponse<Map<String, Object>> upload(@PathVariable("patientId") Long patientId,
                                                   @PathVariable("studyId") Long studyId,
                                                   @Valid @RequestBody FileUploadRequest request,
                                                   HttpServletRequest httpRequest) {
        Long userId = SecurityUtil.currentUserId(httpRequest);
        FileUpload upload = fileService.create(patientId, studyId, request.getFileType(), request.getSizeBytes(), userId, request.getFilePath());
        Map<String, Object> result = new HashMap<>();
        result.put("fileId", upload.getId());
        result.put("filePath", upload.getFilePath());
        return ApiResponse.success(result);
    }

    @PostMapping(value = "/{patientId}/studies/{studyId}/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ApiResponse<Map<String, Object>> uploadFile(@PathVariable("patientId") Long patientId,
                                                       @PathVariable("studyId") Long studyId,
                                                       @RequestParam("file") MultipartFile file,
                                                       @RequestParam(value = "fileType", required = false) String fileType,
                                                       HttpServletRequest httpRequest) {
        if (file == null || file.isEmpty()) {
            return ApiResponse.failure(400, "message");
        }
        String resolvedType = resolveFileType(fileType, file.getOriginalFilename());
        String objectName = buildObjectName(patientId, studyId, resolvedType);
        String url;
        try {
            url = aliOssUtil.upload(file.getBytes(), objectName);
        } catch (IOException e) {
            return ApiResponse.failure(500, "message" + e.getMessage());
        }
        Long userId = SecurityUtil.currentUserId(httpRequest);
        FileUpload upload = fileService.create(patientId, studyId, resolvedType, file.getSize(), userId, url);
        Map<String, Object> result = new HashMap<>();
        result.put("fileId", upload.getId());
        result.put("filePath", upload.getFilePath());
        result.put("objectName", objectName);
        result.put("fileType", resolvedType);
        return ApiResponse.success(result);
    }

    private String resolveFileType(String provided, String originalName) {
        if (StringUtils.hasText(provided)) {
            return provided;
        }
        String ext = StringUtils.getFilenameExtension(originalName);
        return StringUtils.hasText(ext) ? ext : "bin";
    }

    private String buildObjectName(Long patientId, Long studyId, String fileType) {
        StringBuilder name = new StringBuilder("patient/")
                .append(patientId)
                .append("/study/")
                .append(studyId)
                .append("/")
                .append(System.currentTimeMillis());
        if (StringUtils.hasText(fileType)) {
            name.append(".").append(fileType);
        }
        return name.toString();
    }
}
