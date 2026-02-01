package com.yunchuan.smartimage_backend.service;

import com.yunchuan.smartimage_backend.common.BusinessException;
import com.yunchuan.smartimage_backend.entity.ContourResult;
import com.yunchuan.smartimage_backend.mapper.ContourResultMapper;
import com.yunchuan.smartimage_backend.vo.ContourVO;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ContourService {

    private final ContourResultMapper contourResultMapper;

    public ContourService(ContourResultMapper contourResultMapper) {
        this.contourResultMapper = contourResultMapper;
    }

    public List<ContourVO> listByPatient(Long patientId) {
        return contourResultMapper.listByPatientId(patientId).stream()
                .map(this::toVO)
                .collect(Collectors.toList());
    }

    public void updateStatus(Long contourId, String status) {
        ContourResult contour = contourResultMapper.findById(contourId);
        if (contour == null) {
            throw new BusinessException(404, "Invalid request");
        }
        contour.setStatus(status);
        contourResultMapper.update(contour);
    }

    public ContourResult findById(Long contourId) {
        ContourResult contour = contourResultMapper.findById(contourId);
        if (contour == null) {
            throw new BusinessException(404, "Invalid request");
        }
        return contour;
    }

    private ContourVO toVO(ContourResult contour) {
        ContourVO vo = new ContourVO();
        vo.setId(contour.getId());
        vo.setStudyId(contour.getStudyId());
        vo.setType(contour.getType());
        vo.setStatus(contour.getStatus());
        vo.setVersion(contour.getVersion());
        vo.setStoragePath(contour.getStoragePath());
        vo.setConfidenceMap(contour.getConfidenceMap());
        return vo;
    }
}
