package com.yunchuan.smartimage_backend.service;

import com.yunchuan.smartimage_backend.common.BusinessException;
import com.yunchuan.smartimage_backend.entity.PatientStudy;
import com.yunchuan.smartimage_backend.mapper.ContourResultMapper;
import com.yunchuan.smartimage_backend.mapper.PatientStudyMapper;
import com.yunchuan.smartimage_backend.vo.StudyVO;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class StudyService {

    private final PatientStudyMapper patientStudyMapper;
    private final ContourResultMapper contourResultMapper;
    private final FileService fileService;
    private static final DateTimeFormatter TIME_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    public StudyService(PatientStudyMapper patientStudyMapper,
                        ContourResultMapper contourResultMapper,
                        FileService fileService) {
        this.patientStudyMapper = patientStudyMapper;
        this.contourResultMapper = contourResultMapper;
        this.fileService = fileService;
    }

    public List<StudyVO> list(Long patientId) {
        List<PatientStudy> studies = patientStudyMapper.listByPatientId(patientId);
        return studies.stream().map(this::toVO).collect(Collectors.toList());
    }

    public PatientStudy create(Long patientId, String studyUid, String modality, String desc) {
        PatientStudy study = new PatientStudy();
        study.setPatientId(patientId);
        study.setStudyUid(StringUtils.hasText(studyUid) ? studyUid : generateStudyUid());
        study.setModality(modality);
        study.setDescription(desc);
        study.setStatus("processing");
        study.setAcquiredAt(LocalDateTime.now());
        patientStudyMapper.insert(study);
        return study;
    }

    public void update(Long studyId, String studyUid, String modality, String desc, String status) {
        PatientStudy study = patientStudyMapper.findById(studyId);
        if (study == null) {
            throw new BusinessException(404, "Invalid request");
        }
        study.setStudyUid(studyUid != null ? studyUid : study.getStudyUid());
        study.setModality(modality != null ? modality : study.getModality());
        study.setDescription(desc != null ? desc : study.getDescription());
        study.setStatus(status != null ? status : study.getStatus());
        patientStudyMapper.update(study);
    }

    public PatientStudy findById(Long studyId) {
        return patientStudyMapper.findById(studyId);
    }

    public void delete(Long patientId, Long studyId) {
        PatientStudy study = patientStudyMapper.findById(studyId);
        if (study == null || (patientId != null && !patientId.equals(study.getPatientId()))) {
            throw new BusinessException(404, "Invalid request");
        }
        contourResultMapper.deleteByStudyId(studyId);
        fileService.deleteByStudyId(studyId);
        patientStudyMapper.deleteById(studyId);
    }

    private StudyVO toVO(PatientStudy study) {
        StudyVO vo = new StudyVO();
        vo.setId(study.getId());
        vo.setStudyUid(study.getStudyUid());
        vo.setModality(study.getModality());
        vo.setDesc(study.getDescription());
        vo.setStatus(study.getStatus());
        vo.setTime(study.getUpdatedAt() == null ? null : TIME_FORMATTER.format(study.getUpdatedAt()));
        return vo;
    }

    private String generateStudyUid() {
        return "ST" + System.currentTimeMillis();
    }
}
