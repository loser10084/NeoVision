package com.yunchuan.smartimage_backend.controller;

import com.yunchuan.smartimage_backend.common.ApiResponse;
import com.yunchuan.smartimage_backend.dto.ContourStatusUpdateRequest;
import com.yunchuan.smartimage_backend.entity.ContourResult;
import com.yunchuan.smartimage_backend.service.ContourService;
import com.yunchuan.smartimage_backend.vo.ContourVO;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/patients")
public class ContourController {

    private final ContourService contourService;

    public ContourController(ContourService contourService) {
        this.contourService = contourService;
    }

    @GetMapping("/{patientId}/contours")
    public ApiResponse<List<ContourVO>> list(@PathVariable("patientId") Long patientId) {
        return ApiResponse.success(contourService.listByPatient(patientId));
    }

    @PutMapping("/{patientId}/contours/{contourId}")
    public ApiResponse<Void> updateStatus(@PathVariable("contourId") Long contourId,
                                          @Valid @RequestBody ContourStatusUpdateRequest request) {
        contourService.updateStatus(contourId, request.getStatus());
        return ApiResponse.success(null);
    }

    @GetMapping("/{patientId}/contours/{contourId}/download")
    public ApiResponse<Map<String, String>> download(@PathVariable("contourId") Long contourId) {
        ContourResult contour = contourService.findById(contourId);
        Map<String, String> data = new HashMap<>();
        data.put("storagePath", contour.getStoragePath());
        data.put("confidenceMap", contour.getConfidenceMap());
        return ApiResponse.success(data);
    }
}
