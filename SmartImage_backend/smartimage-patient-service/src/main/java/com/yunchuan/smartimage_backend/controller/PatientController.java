package com.yunchuan.smartimage_backend.controller;

import com.yunchuan.smartimage_backend.common.ApiResponse;
import com.yunchuan.smartimage_backend.dto.ContourUpsertRequest;
import com.yunchuan.smartimage_backend.dto.PatientCreateRequest;
import com.yunchuan.smartimage_backend.dto.PatientUpdateRequest;
import com.yunchuan.smartimage_backend.dto.ReviewRequest;
import com.yunchuan.smartimage_backend.entity.Patient;
import com.yunchuan.smartimage_backend.security.SecurityUtil;
import com.yunchuan.smartimage_backend.service.PatientService;
import com.yunchuan.smartimage_backend.vo.PatientDetailVO;
import com.yunchuan.smartimage_backend.vo.PatientSummaryVO;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/patients")
public class PatientController {

    private final PatientService patientService;

    public PatientController(PatientService patientService) {
        this.patientService = patientService;
    }

    @GetMapping
    public ApiResponse<List<PatientSummaryVO>> list(@RequestParam(value = "keyword", required = false) String keyword) {
        return ApiResponse.success(patientService.search(keyword));
    }

    @PostMapping
    public ApiResponse<Patient> create(@Valid @RequestBody PatientCreateRequest request, HttpServletRequest httpRequest) {
        Patient patient = new Patient();
        patient.setName(request.getName());
        patient.setSex(request.getSex());
        patient.setAge(request.getAge());
        patient.setStage(request.getStage());
        patient.setDiagnosis(request.getDiagnosis());
        patient.setAttendingId(SecurityUtil.currentUserId(httpRequest));
        Patient created = patientService.create(patient);
        return ApiResponse.success(created);
    }

    @GetMapping("/{id}")
    public ApiResponse<PatientDetailVO> detail(@PathVariable("id") Long id) {
        return ApiResponse.success(patientService.detail(id));
    }

    @PutMapping("/{id}")
    public ApiResponse<Void> update(@PathVariable("id") Long id, @Valid @RequestBody PatientUpdateRequest request) {
        Patient patient = new Patient();
        patient.setId(id);
        patient.setName(request.getName());
        patient.setSex(request.getSex());
        patient.setAge(request.getAge());
        patient.setStage(request.getStage());
        patient.setDiagnosis(request.getDiagnosis());
        patientService.update(patient);
        return ApiResponse.success(null);
    }

    @DeleteMapping("/{id}")
    public ApiResponse<Void> delete(@PathVariable("id") Long id) {
        patientService.delete(id);
        return ApiResponse.success(null);
    }

    @PostMapping("/{id}/review")
    public ApiResponse<Void> review(@PathVariable("id") Long id, @RequestBody ReviewRequest request, HttpServletRequest httpRequest) {
        if (request.isConfirmed()) {
            patientService.confirmPlan(id, SecurityUtil.currentUserId(httpRequest));
        }
        return ApiResponse.success(null);
    }

    @PostMapping("/{id}/contours/upsert")
    public ApiResponse<Void> upsertContour(@PathVariable("id") Long id,
                                           @RequestBody ContourUpsertRequest request,
                                           HttpServletRequest httpRequest) {
        patientService.upsertContour(id, request, SecurityUtil.currentUserId(httpRequest));
        return ApiResponse.success(null);
    }
}
