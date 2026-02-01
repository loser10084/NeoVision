package com.yunchuan.smartimage_backend.service;

import com.yunchuan.smartimage_backend.common.BusinessException;
import com.yunchuan.smartimage_backend.entity.FileUpload;
import com.yunchuan.smartimage_backend.mapper.FileUploadMapper;
import com.yunchuan.smartimage_backend.vo.FileVO;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class FileService {

    private final FileUploadMapper fileUploadMapper;

    public FileService(FileUploadMapper fileUploadMapper) {
        this.fileUploadMapper = fileUploadMapper;
    }

    public FileUpload create(Long patientId, Long studyId, String fileType, Long sizeBytes, Long uploaderId, String filePath) {
        FileUpload upload = new FileUpload();
        upload.setPatientId(patientId);
        upload.setStudyId(studyId);
        upload.setFileType(fileType);
        upload.setSizeBytes(sizeBytes);
        upload.setUploaderId(uploaderId);
        upload.setFilePath(StringUtils.hasText(filePath) ? filePath : buildDefaultPath(patientId, studyId, fileType));
        fileUploadMapper.insert(upload);
        return upload;
    }

    public FileVO find(Long fileId) {
        FileUpload upload = fileUploadMapper.findById(fileId);
        if (upload == null) {
            throw new BusinessException(404, "Invalid request");
        }
        FileVO vo = new FileVO();
        vo.setId(upload.getId());
        vo.setPatientId(upload.getPatientId());
        vo.setStudyId(upload.getStudyId());
        vo.setFileType(upload.getFileType());
        vo.setFilePath(upload.getFilePath());
        vo.setSize(upload.getSizeBytes());
        return vo;
    }

    public void delete(Long fileId) {
        if (fileUploadMapper.deleteById(fileId) == 0) {
            throw new BusinessException(404, "Invalid request");
        }
    }

    public void deleteByStudyId(Long studyId) {
        fileUploadMapper.deleteByStudyId(studyId);
    }

    private String buildDefaultPath(Long patientId, Long studyId, String fileType) {
        return "/data/patient/" + patientId + "/study/" + studyId + "/" + System.currentTimeMillis() + "." + fileType;
    }
}
