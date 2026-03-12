package com.yunchuan.smartimage_backend.controller;

import com.yunchuan.smartimage_backend.common.ApiResponse;
import com.yunchuan.smartimage_backend.entity.FileUpload;
import com.yunchuan.smartimage_backend.entity.PatientStudy;
import com.yunchuan.smartimage_backend.security.SecurityUtil;
import com.yunchuan.smartimage_backend.service.FileService;
import com.yunchuan.smartimage_backend.service.ModelSegmentService;
import com.yunchuan.smartimage_backend.service.ModelService;
import com.yunchuan.smartimage_backend.service.StudyService;
import com.yunchuan.smartimage_backend.utils.AliOssUtil;
import com.yunchuan.smartimage_backend.vo.ModelVO;
import com.yunchuan.smartimage_backend.vo.StudyArtifactsVO;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.http.MediaType;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/studies")
public class ModelController {

    private final ModelService modelService;
    private final StudyService studyService;
    private final FileService fileService;
    private final AliOssUtil aliOssUtil;
    private final ModelSegmentService modelSegmentService;

    public ModelController(ModelService modelService,
                           StudyService studyService,
                           FileService fileService,
                           AliOssUtil aliOssUtil,
                           ModelSegmentService modelSegmentService) {
        this.modelService = modelService;
        this.studyService = studyService;
        this.fileService = fileService;
        this.aliOssUtil = aliOssUtil;
        this.modelSegmentService = modelSegmentService;
    }

    @GetMapping("/{studyId}/model")
    public ApiResponse<ModelVO> getModel(@PathVariable("studyId") Long studyId) {
        return ApiResponse.success(modelService.getModel(studyId));
    }

    @GetMapping("/{studyId}/artifacts/latest")
    public ApiResponse<StudyArtifactsVO> getLatestArtifacts(@PathVariable("studyId") Long studyId) {
        return ApiResponse.success(modelService.getLatestArtifacts(studyId));
    }

    @GetMapping("/{studyId}/download/volume")
    public void downloadVolume(@PathVariable("studyId") Long studyId, HttpServletResponse response) throws IOException {
        FileUpload volume = modelService.getLatestVolumeFile(studyId);
        if (volume == null || !StringUtils.hasText(volume.getFilePath())) {
            response.sendError(404, "volume not found");
            return;
        }
        response.sendRedirect(appendDownloadHint(volume.getFilePath(), "volume.nrrd"));
    }

    @GetMapping("/{studyId}/download/label")
    public void downloadLabel(@PathVariable("studyId") Long studyId, HttpServletResponse response) throws IOException {
        FileUpload label = modelService.getLatestLabelFile(studyId);
        if (label == null || !StringUtils.hasText(label.getFilePath())) {
            response.sendError(404, "label not found");
            return;
        }
        response.sendRedirect(appendDownloadHint(label.getFilePath(), "label.nrrd"));
    }

    @PostMapping(value = "/{studyId}/segment", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ApiResponse<Map<String, Object>> segmentStudy(@PathVariable("studyId") Long studyId,
                                                         @RequestParam("file") MultipartFile file,
                                                         HttpServletRequest httpRequest) {
        if (file == null || file.isEmpty()) {
            return ApiResponse.failure(400, "empty file");
        }
        PatientStudy study = studyService.findById(studyId);
        if (study == null) {
            return ApiResponse.failure(404, "study not found");
        }

        Long patientId = study.getPatientId();
        Long userId = SecurityUtil.currentUserId(httpRequest);

        byte[] volumeBytes;
        try {
            volumeBytes = file.getBytes();
        } catch (IOException e) {
            return ApiResponse.failure(500, "read file failed: " + e.getMessage());
        }

        String volumeType = "volume.nrrd";
        String volumeObject = buildObjectName(patientId, studyId, volumeType);
        String volumeUrl;
        try {
            volumeUrl = aliOssUtil.upload(volumeBytes, volumeObject);
        } catch (Exception e) {
            return ApiResponse.failure(500, "upload volume failed: " + e.getMessage());
        }

        byte[] labelBytes;
        try {
            labelBytes = modelSegmentService.segmentNrrd(volumeBytes, file.getOriginalFilename());
        } catch (Exception e) {
            return ApiResponse.failure(500, "model inference failed: " + e.getMessage());
        }

        String labelType = "label.nrrd";
        String labelObject = buildObjectName(patientId, studyId, labelType);
        String labelUrl;
        try {
            labelUrl = aliOssUtil.upload(labelBytes, labelObject);
        } catch (Exception e) {
            return ApiResponse.failure(500, "upload label failed: " + e.getMessage());
        }

        FileUpload volumeUpload = fileService.create(patientId, studyId, volumeType, file.getSize(), userId, volumeUrl);
        FileUpload labelUpload = fileService.create(patientId, studyId, labelType, (long) labelBytes.length, userId, labelUrl);

        Map<String, Object> result = new HashMap<>();
        result.put("volumeUrl", volumeUrl);
        result.put("labelUrl", labelUrl);
        result.put("volumeFileId", volumeUpload.getId());
        result.put("labelFileId", labelUpload.getId());
        result.put("volumeType", volumeType);
        result.put("labelType", labelType);
        return ApiResponse.success(result);
    }

    @PostMapping(value = "/{studyId}/segment/multimodal", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public ApiResponse<Map<String, Object>> segmentStudyMultimodal(@PathVariable("studyId") Long studyId,
                                                                   @RequestParam("flair") MultipartFile flair,
                                                                   @RequestParam("t1") MultipartFile t1,
                                                                   @RequestParam("t1c") MultipartFile t1c,
                                                                   @RequestParam("t2") MultipartFile t2,
                                                                   HttpServletRequest httpRequest) {
        if (flair == null || flair.isEmpty() ||
                t1 == null || t1.isEmpty() ||
                t1c == null || t1c.isEmpty() ||
                t2 == null || t2.isEmpty()) {
            return ApiResponse.failure(400, "empty file");
        }
        PatientStudy study = studyService.findById(studyId);
        if (study == null) {
            return ApiResponse.failure(404, "study not found");
        }

        Long patientId = study.getPatientId();
        Long userId = SecurityUtil.currentUserId(httpRequest);

        byte[] flairBytes;
        byte[] t1Bytes;
        byte[] t1cBytes;
        byte[] t2Bytes;
        try {
            flairBytes = flair.getBytes();
            t1Bytes = t1.getBytes();
            t1cBytes = t1c.getBytes();
            t2Bytes = t2.getBytes();
        } catch (IOException e) {
            return ApiResponse.failure(500, "read file failed: " + e.getMessage());
        }
        String invalid = firstInvalidNrrd(flairBytes, t1Bytes, t1cBytes, t2Bytes);
        if (invalid != null) {
            String detail = nrrdMagicLineFor(invalid, flairBytes, t1Bytes, t1cBytes, t2Bytes);
            return ApiResponse.failure(400, "invalid nrrd: " + invalid + (detail == null ? "" : (" (" + detail + ")")));
        }

        String flairType = "volume.flair.nrrd";
        String t1Type = "volume.t1.nrrd";
        String t1cType = "volume.t1c.nrrd";
        String t2Type = "volume.t2.nrrd";

        String flairUrl;
        String t1Url;
        String t1cUrl;
        String t2Url;
        try {
            flairUrl = aliOssUtil.upload(flairBytes, buildObjectName(patientId, studyId, flairType));
            t1Url = aliOssUtil.upload(t1Bytes, buildObjectName(patientId, studyId, t1Type));
            t1cUrl = aliOssUtil.upload(t1cBytes, buildObjectName(patientId, studyId, t1cType));
            t2Url = aliOssUtil.upload(t2Bytes, buildObjectName(patientId, studyId, t2Type));
        } catch (Exception e) {
            return ApiResponse.failure(500, "upload volume failed: " + e.getMessage());
        }

        byte[] labelBytes;
        try {
            labelBytes = modelSegmentService.segmentMultimodal(
                    flairBytes, flair.getOriginalFilename(),
                    t1Bytes, t1.getOriginalFilename(),
                    t1cBytes, t1c.getOriginalFilename(),
                    t2Bytes, t2.getOriginalFilename()
            );
        } catch (Exception e) {
            return ApiResponse.failure(500, "model inference failed: " + e.getMessage());
        }

        String labelType = "label.nrrd";
        String labelUrl;
        try {
            labelUrl = aliOssUtil.upload(labelBytes, buildObjectName(patientId, studyId, labelType));
        } catch (Exception e) {
            return ApiResponse.failure(500, "upload label failed: " + e.getMessage());
        }

        FileUpload flairUpload = fileService.create(patientId, studyId, flairType, flair.getSize(), userId, flairUrl);
        FileUpload t1Upload = fileService.create(patientId, studyId, t1Type, t1.getSize(), userId, t1Url);
        FileUpload t1cUpload = fileService.create(patientId, studyId, t1cType, t1c.getSize(), userId, t1cUrl);
        FileUpload t2Upload = fileService.create(patientId, studyId, t2Type, t2.getSize(), userId, t2Url);
        FileUpload labelUpload = fileService.create(patientId, studyId, labelType, (long) labelBytes.length, userId, labelUrl);

        Map<String, Object> result = new HashMap<>();
        result.put("flairUrl", flairUrl);
        result.put("t1Url", t1Url);
        result.put("t1cUrl", t1cUrl);
        result.put("t2Url", t2Url);
        result.put("labelUrl", labelUrl);
        result.put("flairFileId", flairUpload.getId());
        result.put("t1FileId", t1Upload.getId());
        result.put("t1cFileId", t1cUpload.getId());
        result.put("t2FileId", t2Upload.getId());
        result.put("labelFileId", labelUpload.getId());
        result.put("labelType", labelType);
        return ApiResponse.success(result);
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

    private String appendDownloadHint(String url, String filename) {
        if (!StringUtils.hasText(url)) {
            return url;
        }
        String encoded = filename == null ? "" : filename.replace(" ", "%20");
        String suffix = "response-content-disposition=attachment%3Bfilename%3D" + encoded;
        if (url.contains("?")) {
            return url + "&" + suffix;
        }
        return url + "?" + suffix;
    }

    private String firstInvalidNrrd(byte[] flairBytes, byte[] t1Bytes, byte[] t1cBytes, byte[] t2Bytes) {
        if (!isNrrd(flairBytes)) return "flair";
        if (!isNrrd(t1Bytes)) return "t1";
        if (!isNrrd(t1cBytes)) return "t1c";
        if (!isNrrd(t2Bytes)) return "t2";
        return null;
    }

    private boolean isNrrd(byte[] bytes) {
        if (bytes == null || bytes.length < 4) {
            return false;
        }
        int i = 0;
        if (bytes.length >= 3 && (bytes[0] & 0xFF) == 0xEF && (bytes[1] & 0xFF) == 0xBB && (bytes[2] & 0xFF) == 0xBF) {
            i = 3;
        }
        StringBuilder sb = new StringBuilder();
        while (i < bytes.length) {
            byte b = bytes[i++];
            if (b == '\n' || b == '\r') {
                break;
            }
            sb.append((char) b);
        }
        return sb.toString().trim().startsWith("NRRD");
    }

    private String nrrdMagicLineFor(String key, byte[] flairBytes, byte[] t1Bytes, byte[] t1cBytes, byte[] t2Bytes) {
        byte[] target;
        switch (key) {
            case "flair":
                target = flairBytes;
                break;
            case "t1":
                target = t1Bytes;
                break;
            case "t1c":
                target = t1cBytes;
                break;
            case "t2":
                target = t2Bytes;
                break;
            default:
                return null;
        }
        if (target == null || target.length == 0) {
            return "empty";
        }
        int i = 0;
        if (target.length >= 3 && (target[0] & 0xFF) == 0xEF && (target[1] & 0xFF) == 0xBB && (target[2] & 0xFF) == 0xBF) {
            i = 3;
        }
        StringBuilder sb = new StringBuilder();
        while (i < target.length && sb.length() < 64) {
            byte b = target[i++];
            if (b == '\n' || b == '\r') {
                break;
            }
            sb.append((char) b);
        }
        return sb.toString().trim();
    }
}
