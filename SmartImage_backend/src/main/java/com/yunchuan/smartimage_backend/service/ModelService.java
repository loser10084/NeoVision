package com.yunchuan.smartimage_backend.service;

import com.yunchuan.smartimage_backend.common.BusinessException;
import com.yunchuan.smartimage_backend.entity.PatientStudy;
import com.yunchuan.smartimage_backend.mapper.PatientStudyMapper;
import com.yunchuan.smartimage_backend.vo.ModelVO;
import org.springframework.stereotype.Service;

@Service
public class ModelService {

    private final PatientStudyMapper patientStudyMapper;

    public ModelService(PatientStudyMapper patientStudyMapper) {
        this.patientStudyMapper = patientStudyMapper;
    }

    public ModelVO getModel(Long studyId) {
        PatientStudy study = patientStudyMapper.findById(studyId);
        if (study == null) {
            throw new BusinessException(404, "影像序列不存在");
        }
        ModelVO vo = new ModelVO();
        vo.setModelPath("/models/" + studyId + "/model.glb");
        vo.setHeatmapPath("/models/" + studyId + "/heatmap.png");
        vo.setOarPath("/models/" + studyId + "/oar.glb");
        vo.setH5Url("/viewer/index.html?studyId=" + studyId);
        return vo;
    }
}
