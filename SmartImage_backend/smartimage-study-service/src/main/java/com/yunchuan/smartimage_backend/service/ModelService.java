package com.yunchuan.smartimage_backend.service;

import com.yunchuan.smartimage_backend.common.BusinessException;
import com.yunchuan.smartimage_backend.entity.FileUpload;
import com.yunchuan.smartimage_backend.entity.PatientStudy;
import com.yunchuan.smartimage_backend.mapper.FileUploadMapper;
import com.yunchuan.smartimage_backend.mapper.PatientStudyMapper;
import com.yunchuan.smartimage_backend.vo.ModelVO;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class ModelService {

    private final PatientStudyMapper patientStudyMapper;
    private final FileUploadMapper fileUploadMapper;

    public ModelService(PatientStudyMapper patientStudyMapper, FileUploadMapper fileUploadMapper) {
        this.patientStudyMapper = patientStudyMapper;
        this.fileUploadMapper = fileUploadMapper;
    }

    public ModelVO getModel(Long studyId) {
        PatientStudy study = patientStudyMapper.findById(studyId);
        if (study == null) {
            throw new BusinessException(404, "message");
        }
        List<FileUpload> uploads = fileUploadMapper.listByStudyId(studyId);
        FileUpload volumeFile = pickPreferredVolume(uploads);
        FileUpload labelFile = pickLatest(uploads, FileRole.LABEL);
        FileUpload heatmapFile = pickLatest(uploads, FileRole.HEATMAP);
        FileUpload modelFile = pickLatest(uploads, FileRole.MODEL);
        FileUpload oarFile = pickLatest(uploads, FileRole.OAR);

        ModelVO vo = new ModelVO();
        if (volumeFile != null) {
            vo.setVolumeUrl(volumeFile.getFilePath());
            vo.setModelPath(volumeFile.getFilePath());
        }
        if (labelFile != null) {
            vo.setLabelUrl(labelFile.getFilePath());
        }
        if (heatmapFile != null) {
            vo.setHeatmapUrl(heatmapFile.getFilePath());
            vo.setHeatmapPath(heatmapFile.getFilePath());
        }
        if (modelFile != null) {
            vo.setModelUrl(modelFile.getFilePath());
            if (vo.getModelPath() == null) {
                vo.setModelPath(modelFile.getFilePath());
            }
        }
        if (oarFile != null) {
            vo.setOarUrl(oarFile.getFilePath());
            vo.setOarPath(oarFile.getFilePath());
        }
        vo.setH5Url("/viewer/index.html?studyId=" + studyId);
        return vo;
    }

    public FileUpload getLatestVolumeFile(Long studyId) {
        List<FileUpload> uploads = fileUploadMapper.listByStudyId(studyId);
        return pickPreferredVolume(uploads);
    }

    public FileUpload getLatestLabelFile(Long studyId) {
        List<FileUpload> uploads = fileUploadMapper.listByStudyId(studyId);
        return pickLatest(uploads, FileRole.LABEL);
    }

    private FileUpload pickLatest(List<FileUpload> uploads, FileRole role) {
        if (uploads == null || uploads.isEmpty()) {
            return null;
        }
        for (FileUpload upload : uploads) {
            String type = normalizeType(upload.getFileType());
            if (matchesRole(type, role)) {
                return upload;
            }
        }
        return null;
    }

    private FileUpload pickPreferredVolume(List<FileUpload> uploads) {
        if (uploads == null || uploads.isEmpty()) {
            return null;
        }
        FileUpload fallback = null;
        for (FileUpload upload : uploads) {
            String type = normalizeType(upload.getFileType());
            if (!matchesRole(type, FileRole.VOLUME)) {
                continue;
            }
            if (fallback == null) {
                fallback = upload;
            }
            if (type.contains("flair") || type.equals("volume") || type.endsWith("volume.nrrd")) {
                return upload;
            }
        }
        return fallback;
    }

    private boolean matchesRole(String type, FileRole role) {
        if (!hasText(type)) {
            return false;
        }
        switch (role) {
            case VOLUME:
                if (isRole(type, "label") || isRole(type, "seg") || isRole(type, "mask")) {
                    return false;
                }
                return isRole(type, "volume")
                        || hasExtension(type, "nrrd")
                        || hasExtension(type, "mha")
                        || hasExtension(type, "nii")
                        || hasExtension(type, "nii.gz");
            case LABEL:
                return isRole(type, "label") || isRole(type, "seg") || isRole(type, "mask");
            case HEATMAP:
                return isRole(type, "heatmap") || isRole(type, "confidence")
                        || hasExtension(type, "png") || hasExtension(type, "jpg") || hasExtension(type, "jpeg");
            case MODEL:
                return isRole(type, "model") || hasExtension(type, "glb") || hasExtension(type, "gltf")
                        || hasExtension(type, "obj") || hasExtension(type, "stl");
            case OAR:
                return isRole(type, "oar");
            default:
                return false;
        }
    }

    private boolean isRole(String type, String role) {
        return type.equals(role) || type.startsWith(role + ".");
    }

    private boolean hasExtension(String type, String ext) {
        if (!hasText(type) || !hasText(ext)) {
            return false;
        }
        String lowerExt = ext.toLowerCase();
        if (type.equals(lowerExt)) {
            return true;
        }
        return type.endsWith("." + lowerExt);
    }

    private boolean hasText(String value) {
        return value != null && !value.trim().isEmpty();
    }

    private String normalizeType(String type) {
        return type == null ? "" : type.trim().toLowerCase();
    }

    private enum FileRole {
        VOLUME,
        LABEL,
        HEATMAP,
        MODEL,
        OAR
    }
}
