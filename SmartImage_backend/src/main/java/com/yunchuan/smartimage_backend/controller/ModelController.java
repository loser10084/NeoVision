package com.yunchuan.smartimage_backend.controller;

import com.yunchuan.smartimage_backend.common.ApiResponse;
import com.yunchuan.smartimage_backend.service.ModelService;
import com.yunchuan.smartimage_backend.vo.ModelVO;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/studies")
public class ModelController {

    private final ModelService modelService;

    public ModelController(ModelService modelService) {
        this.modelService = modelService;
    }

    @GetMapping("/{studyId}/model")
    public ApiResponse<ModelVO> getModel(@PathVariable("studyId") Long studyId) {
        return ApiResponse.success(modelService.getModel(studyId));
    }
}
