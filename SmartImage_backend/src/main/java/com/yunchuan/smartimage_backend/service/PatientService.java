package com.yunchuan.smartimage_backend.service;

import com.yunchuan.smartimage_backend.common.BusinessException;
import com.yunchuan.smartimage_backend.entity.ContourResult;
import com.yunchuan.smartimage_backend.entity.Patient;
import com.yunchuan.smartimage_backend.entity.PatientStudy;
import com.yunchuan.smartimage_backend.mapper.ContourResultMapper;
import com.yunchuan.smartimage_backend.mapper.PatientMapper;
import com.yunchuan.smartimage_backend.mapper.PatientStudyMapper;
import com.yunchuan.smartimage_backend.vo.PatientDetailVO;
import com.yunchuan.smartimage_backend.vo.PatientSummaryVO;
import org.springframework.stereotype.Service;
import org.springframework.util.CollectionUtils;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
public class PatientService {

    private final PatientMapper patientMapper;
    private final PatientStudyMapper patientStudyMapper;
    private final ContourResultMapper contourResultMapper;

    private static final DateTimeFormatter TIME_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    public PatientService(PatientMapper patientMapper, PatientStudyMapper patientStudyMapper, ContourResultMapper contourResultMapper) {
        this.patientMapper = patientMapper;
        this.patientStudyMapper = patientStudyMapper;
        this.contourResultMapper = contourResultMapper;
    }

    public List<PatientSummaryVO> search(String keyword) {
        List<Patient> patients = patientMapper.search(keyword);
        return patients.stream().map(this::buildSummary).collect(Collectors.toList());
    }

    public PatientDetailVO detail(Long id) {
        Patient patient = patientMapper.findById(id);
        if (patient == null) {
            throw new BusinessException(404, "患者不存在");
        }
        return buildDetail(patient);
    }

    public Patient create(Patient patient) {
        patient.setPatientNo(generatePatientNo());
        patientMapper.insert(patient);
        return patient;
    }

    public void update(Patient patient) {
        if (patientMapper.update(patient) == 0) {
            throw new BusinessException(404, "患者不存在");
        }
    }

    public void delete(Long id) {
        patientMapper.delete(id);
    }

    public void confirmPlan(Long patientId, Long userId) {
        List<ContourResult> contours = contourResultMapper.listByPatientId(patientId);
        if (CollectionUtils.isEmpty(contours)) {
            throw new BusinessException(400, "暂无可确认的靶区结果");
        }
        contours.forEach(c -> {
            c.setStatus("已确认");
            contourResultMapper.update(c);
        });
    }

    private PatientSummaryVO buildSummary(Patient patient) {
        List<ContourResult> contours = contourResultMapper.listByPatientId(patient.getId());
        List<PatientStudy> studies = patientStudyMapper.listByPatientId(patient.getId());
        PatientSummaryVO vo = new PatientSummaryVO();
        vo.setId(patient.getId());
        vo.setPatientNo(patient.getPatientNo());
        vo.setName(patient.getName());
        vo.setSex(patient.getSex());
        vo.setAge(patient.getAge());
        vo.setStage(patient.getStage());
        vo.setDiagnosis(patient.getDiagnosis());
        vo.setStudyId(studies.isEmpty() ? null : String.valueOf(studies.get(0).getId()));
        vo.setStatus(determineStatus(studies, contours));
        vo.setGtvReady(hasType(contours, "GTV"));
        vo.setCtvReady(hasType(contours, "CTV"));
        vo.setLastUpdate(formatTime(patient.getUpdatedAt()));
        return vo;
    }

    private PatientDetailVO buildDetail(Patient patient) {
        List<ContourResult> contours = contourResultMapper.listByPatientId(patient.getId());
        List<PatientStudy> studies = patientStudyMapper.listByPatientId(patient.getId());
        PatientDetailVO vo = new PatientDetailVO();
        vo.setId(patient.getId());
        vo.setPatientNo(patient.getPatientNo());
        vo.setName(patient.getName());
        vo.setSex(patient.getSex());
        vo.setAge(patient.getAge());
        vo.setStage(patient.getStage());
        vo.setDiagnosis(patient.getDiagnosis());
        vo.setStudyId(studies.isEmpty() ? null : String.valueOf(studies.get(0).getId()));
        vo.setStatus(determineStatus(studies, contours));
        vo.setGtvReady(hasType(contours, "GTV"));
        vo.setCtvReady(hasType(contours, "CTV"));
        vo.setGtv(getPathByType(contours, "GTV"));
        vo.setCtv(getPathByType(contours, "CTV"));
        vo.setLastUpdate(formatTime(patient.getUpdatedAt()));
        return vo;
    }

    private boolean hasType(List<ContourResult> contours, String type) {
        return contours.stream().anyMatch(c -> type.equalsIgnoreCase(c.getType()));
    }

    private String getPathByType(List<ContourResult> contours, String type) {
        Optional<ContourResult> result = contours.stream()
                .filter(c -> type.equalsIgnoreCase(c.getType()))
                .findFirst();
        return result.map(ContourResult::getStoragePath).orElse(null);
    }

    private String determineStatus(List<PatientStudy> studies, List<ContourResult> contours) {
        if (!CollectionUtils.isEmpty(contours)) {
            return contours.stream().allMatch(c -> "已确认".equals(c.getStatus())) ? "已确认" : "处理中";
        }
        if (!CollectionUtils.isEmpty(studies)) {
            return "待处理";
        }
        return "待上传影像";
    }

    private String formatTime(LocalDateTime time) {
        return time == null ? null : TIME_FORMATTER.format(time);
    }

    private String generatePatientNo() {
        return "P" + DateTimeFormatter.ofPattern("yyyyMMddHHmmss").format(LocalDateTime.now());
    }
}
